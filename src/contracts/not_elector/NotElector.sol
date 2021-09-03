/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";
import "../libraries/Errors.sol";

contract NotElector is INotElector {

    // EVENTS
    event electionIsOverEvent();
    event oneUSDCostCalculatedEvent(uint128 oneUSDCost, uint time);
    event oneUSDCostCalculationStarted(uint time);
    event notValidatorSlashed(address _address);
    event oops(Quotation[] xs);

    // ENUMS
    enum Status {
        electionIsInProgress,
        validation,
        revealingMode,
        validationIsOver
    }

    // STATUS
    Status public status;
    uint revealingStartTime;

    // DATA (election)
    mapping(address => uint128) notValidatorsStake;

    // DATA (regular validation)
    uint256 random;
    uint lastNow;
    mapping(address => uint128) public notValidatorsRank;
    mapping(address => uint) lastQuotationTime;
    mapping(address => uint256) lastQuotationHash;
    mapping(address => uint) badChecksInARow;

    // DATA (revealing mode)
    mapping(address => uint256) quotationsToReveal;
    mapping(address => uint128) revealedQuotations;

    // PARAMS
    uint public signUpStageBeginning;
    uint public signUpStageDuration;
    uint public validationStageBeginning;
    uint public validationStageDuration;

    // COSTS AND BALANCES
    uint128 constant SLASH_COST = 1 ton;
    // max balance at which the commission is charged
    uint128 constant MIN_BALANCE = 1 ton;
    uint128 constant SET_QUOTATION_COMISSION = 0.3 ton;
    uint128 constant MIN_STAKE_SIZE = 10 kiloton; // КОСТЫЛЬ!

    // OTHER CONSTANTS
    uint constant REVEAL_FREQUENCY_FACTOR = 2;
    uint constant REVEALING_MODE_DURATION = 5;
    uint constant QUOTATION_LIFETIME = 5;
    uint constant NUMBER_OF_CHECKS_BEFORE_BAN = 3;

    // METHODS
    constructor(
        uint signUpStageBeginningArg,
        uint signUpStageDurationArg,
        uint validationStageBeginningArg,
        uint validationStageDurationArg
    ) public {
        require(tvm.pubkey() != 0, Errors.NO_PUB_KEY);
        require(tvm.pubkey() == msg.pubkey(), Errors.WRONG_PUB_KEY);
        tvm.accept();

        signUpStageBeginning = signUpStageBeginningArg;
        signUpStageDuration = signUpStageDurationArg;
        validationStageBeginning = validationStageBeginningArg;
        validationStageDuration = validationStageDurationArg;
        status = Status.electionIsInProgress;
    }

    // ELECTION PHASE
    function signUp(
        uint128 stakeSize,
        uint validationStartTime,
        uint validationDuration
    ) override external transferRemainingValueBack {
        require(
            (validationStartTime == validationStageBeginning) &&
                (validationDuration == validationStageDuration),
            Errors.VALIDATOR_HAS_INCORRECT_PARAMS
        );

        notValidatorsStake[msg.sender] = stakeSize;
    }

    function endElection() override external {
        require(now > signUpStageBeginning + signUpStageDuration, Errors.WRONG_MOMENT);
        require(status == Status.electionIsInProgress);
        tvm.accept();

        for ((address notValidator, uint stakeSize) : notValidatorsStake) {
            // TODO algorithm can be different!!!!
            if (stakeSize >= MIN_STAKE_SIZE) {
                notValidatorsRank[notValidator] = 0;
            }
        }

        emit electionIsOverEvent();
        status = Status.validation;
    }

    // VALIDATION PHASE
    function setQuotation(
        uint256 hashedQuotation
    ) override external takeComissionAndTransferRemainingValueBack {
        require(notValidatorsRank.exists(msg.sender), Errors.WRONG_SENDER);

        lastQuotationHash[msg.sender] = hashedQuotation;
        lastQuotationTime[msg.sender] = now;

        TvmBuilder builder;
        builder.store(random, hashedQuotation);
        random = tvm.hash(builder.toCell());

        if ((now != lastNow) && (status == Status.validation) && ((random % REVEAL_FREQUENCY_FACTOR) == 0)) {
            turnOnRevealingMode();
        }

        if (status == Status.revealingMode) {
            if ((now - revealingStartTime) > REVEALING_MODE_DURATION) {
                calcFinalQuotation();
            }
        }

        lastNow = now;
    }

    function revealQuotation(
        uint128 oneUSDCost,
        uint256 salt
    ) override external transferRemainingValueBack {
        require(notValidatorsRank.exists(msg.sender), Errors.WRONG_SENDER);
        require(status == Status.revealingMode, Errors.NOT_REVEALING_MODE);
        require(quotationsToReveal.exists(msg.sender), Errors.NOTHING_TO_REVEAL);

        uint256 quotationHash = quotationsToReveal[msg.sender];
        require(
            saltedCostHash(oneUSDCost, salt) == quotationHash,
            Errors.INCORRECT_REVEAL_DATA
        );

        revealedQuotations[msg.sender] = oneUSDCost;
        delete quotationsToReveal[msg.sender];
        if (quotationsToReveal.empty()) {
            calcFinalQuotation();
        }
    }


    struct Quotation {address notValidator; uint128 value;}

    function calcFinalQuotation() private inline {
        Quotation[] quotations = qSortedQuotations();
        uint n = quotations.length;

        uint128 v_25 = quotations[(n - 1) / 4].value;
        uint128 v_50 = quotations[n / 2].value;
        uint128 v_75 = quotations[(3 * (n - 1)) / 4].value;

        for (uint i = 0; i < n; i++) {
            uint128 P; // P=10^9 means probability=1
            Quotation quotation = quotations[i];
            if (quotation.value < v_25 && n > 3) {
                P = uint128(i * 1000000000 / (n / 4));
            } else if (quotation.value > v_75 && n > 3) {
                P = uint128((n - i - 1) * 1000000000 / (n / 4));
            } else {
                P = 1000000000;
            }

            uint128 r = notValidatorsRank[quotation.notValidator];
            uint128 r_c = 1000000000 - P;

            // here constant a = 2/7
            uint128 r_new = (5*r / 7) + (2*r_c / 7);
            if (r_new >= 500000000) {
                uint badChecks = badChecksInARow[quotation.notValidator];
                if (badChecks + 1 == NUMBER_OF_CHECKS_BEFORE_BAN) {
                    INotValidator(quotation.notValidator).slash();
                    emit notValidatorSlashed(quotation.notValidator);
                    delete notValidatorsRank[quotation.notValidator];
                    delete revealedQuotations[quotation.notValidator];
                    delete badChecksInARow[quotation.notValidator];
                    delete quotationsToReveal[quotation.notValidator];
                } else {
                    badChecksInARow[quotation.notValidator] += 1;
                    notValidatorsRank[quotation.notValidator] = r_new;
                }
            } else {
                notValidatorsRank[quotation.notValidator] = r_new;
                delete badChecksInARow[quotation.notValidator];
            }
        }

        for ((address notValidator,) : quotationsToReveal) {
            uint128 r = notValidatorsRank[notValidator];
            uint128 r_c = 1000000000;

            // here constant a = 2/7
            uint128 r_new = (5*r / 7) + (2*r_c / 7);
            if (r_new >= 500000000) {
                uint badChecks = badChecksInARow[notValidator];
                if (badChecks + 1 == NUMBER_OF_CHECKS_BEFORE_BAN) {
                    INotValidator(notValidator).slash();
                    emit notValidatorSlashed(notValidator);
                    delete notValidatorsRank[notValidator];
                    delete revealedQuotations[notValidator];
                    delete badChecksInARow[notValidator];
                    delete quotationsToReveal[notValidator];
                } else {
                    badChecksInARow[notValidator] += 1;
                    notValidatorsRank[notValidator] = r_new;
                }
            } else {
                notValidatorsRank[notValidator] = r_new;
                delete badChecksInARow[notValidator];
            }
        }

        emit oneUSDCostCalculatedEvent(v_50, now - validationStageBeginning);
        status = Status.validation;
        // TODO send necessery data to NOT-Bank
    }

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) override external {
        require(tvm.pubkey() == msg.pubkey(), Errors.WRONG_PUB_KEY);
        require(now > validationStageBeginning + validationStageDuration);
        tvm.accept();

        selfdestruct(destination);
    }

    // INLINES
    function turnOnRevealingMode() inline private {
        mapping(address => uint256) tempQuotationsToReveal;
        uint256 h;
        for ((address notValidator, uint time) : lastQuotationTime) {
            if (now - time <= QUOTATION_LIFETIME) {
                h = lastQuotationHash[notValidator];
                tempQuotationsToReveal[notValidator] = h;
                INotValidator(notValidator).requestRevealing(h);
            }
        }

        quotationsToReveal = tempQuotationsToReveal;
        status = Status.revealingMode;
        revealingStartTime = now;

        delete revealedQuotations;
        delete lastQuotationTime;
        delete lastQuotationHash;
    }

    function saltedCostHash(
        uint128 cost,
        uint256 salt
    ) inline private returns (uint256) {
        // TODO gas optimization...
        TvmBuilder builder;
        builder.store(cost, salt);
        return tvm.hash(builder.toCell());
    }

    struct Boundaries{uint l; uint r;}
    function qSortedQuotations() inline private returns (Quotation[] res) {
        for ((address notValidator, uint128 value) : revealedQuotations) {
            res.push(Quotation(notValidator, value));
        }

        vector(Boundaries) s;
        s.push(Boundaries(0, res.length - 1));

        uint l;
        uint r;
        uint i;
        uint j;
        Quotation none;
        uint128 v;
        while (!s.empty()) {
            (l, r) = s.pop().unpack();
            if (r > l) {
                v = res[(l + r) / 2].value;
                i = l;
                j = r;
                while (i <= j) {
                    while (res[i].value < v){
                        i++;
                    }
                    while (res[j].value > v){
                        j--;
                    }
                    if (i >= j)
                        break;
                    none = res[i];
                    res[i] = res[j];
                    res[j] = none;
                    i++;
                    j--;
                }
                i = j;

                s.push(Boundaries(i + 1, r));
                s.push(Boundaries(l, i));
            }
        }

        uint128 prev;
        for (i = 0; i < res.length; i++) {
            if (res[uint(i)].value < prev) {
                emit oops(res);
            }
            prev = res[i].value;
        }
    }

    // MODIFIERS
    modifier transferRemainingValueBack {
        _;
        msg.sender.transfer({value: 0 ton, flag: 64});
    }

    modifier takeComissionAndTransferRemainingValueBack {
        _;
        if (address(this).balance > MIN_BALANCE) {
            msg.sender.transfer({value: 0 ton, flag: 64});
        } else {
            msg.sender.transfer(msg.value - SET_QUOTATION_COMISSION);
        }
    }
}
