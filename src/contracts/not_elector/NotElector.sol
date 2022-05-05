/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";
import "../libraries/Errors.sol";

abstract contract NotElector is INotElector {

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
    uint notValidatorsRankSize;
    mapping(address => uint) badChecksInARow;

    // DATA (revealing mode)
    mapping(address => uint128) revealedQuotations;
    uint quotationsToReveal;

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
    uint constant REVEAL_MIN_INTERVAL = 7 days;  // added
    uint constant REVEAL_FREQUENCY_FACTOR = 2;
    uint constant REVEALING_MODE_DURATION = 5;
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
                notValidatorsRankSize += 1;
                INotValidator(notValidator).setIsElected{value: 0.1 ton, flag: 1, bounce: false}(true);  // fixed
            } else {
                INotValidator(notValidator).setIsElected{value: 0.1 ton, flag: 1, bounce: false}(false);  // fixed
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

        TvmBuilder builder;
        builder.store(random, hashedQuotation);
        random = tvm.hash(builder.toCell());

        // added
        if ((now != lastNow) &&
            (status == Status.validation) &&
            (random % REVEAL_FREQUENCY_FACTOR == 0) &&
            (now - revealingStartTime > REVEAL_MIN_INTERVAL)
        ) {
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
        uint128 oneUSDCost
    ) override external transferRemainingValueBack {
        require(notValidatorsRank.exists(msg.sender), Errors.WRONG_SENDER);
        require(status == Status.revealingMode, Errors.NOT_REVEALING_MODE);
        require(revealedQuotations[msg.sender] == 0, Errors.ALREADY_REVEALED);

        revealedQuotations[msg.sender] = oneUSDCost;
        quotationsToReveal -= 1;
        if (quotationsToReveal == 0) {
            calcFinalQuotation();
        }
    }

    function quotationIsTooOld() override external transferRemainingValueBack {
        require(notValidatorsRank.exists(msg.sender), Errors.WRONG_SENDER);
        require(status == Status.revealingMode, Errors.NOT_REVEALING_MODE);

        delete revealedQuotations[msg.sender];
        quotationsToReveal -= 1;
        if (quotationsToReveal == 0) {
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
                    notValidatorsRankSize -= 1;
                    delete badChecksInARow[quotation.notValidator];
                } else {
                    badChecksInARow[quotation.notValidator] += 1;
                    notValidatorsRank[quotation.notValidator] = r_new;
                }
            } else {
                notValidatorsRank[quotation.notValidator] = r_new;
                delete badChecksInARow[quotation.notValidator];
            }
        }

        for ((address notValidator, uint128 value) : revealedQuotations) {
            if (value == 0) {
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
                        notValidatorsRankSize -= 1;
                        delete badChecksInARow[notValidator];
                    } else {
                        badChecksInARow[notValidator] += 1;
                        notValidatorsRank[notValidator] = r_new;
                    }
                } else {
                    notValidatorsRank[notValidator] = r_new;
                    delete badChecksInARow[notValidator];
                }
            }
        }

        emit oneUSDCostCalculatedEvent(v_50, now - validationStageBeginning);
        status = Status.validation;
        delete revealedQuotations;

        _afterRevealing(v_50);  // added
        // TODO send necessery data to NOT-Bank
    }

    function _afterRevealing(uint128 quotingPrice) internal virtual;  // added

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
        for ((address notValidator,) : notValidatorsRank) {
            INotValidator(notValidator).requestRevealing{value: 0.1 ton, flag: 1, bounce: false}();  // fixed
            revealedQuotations[notValidator] = 0;
        }

        status = Status.revealingMode;
        revealingStartTime = now;
        quotationsToReveal = notValidatorsRankSize;
    }

    struct Boundaries{uint l; uint r;}
    function qSortedQuotations() inline private returns (Quotation[] res) {
        for ((address notValidator, uint128 value) : revealedQuotations) {
            if (value != 0) {
                res.push(Quotation(notValidator, value));
            }
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
