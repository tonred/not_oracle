/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";
import "../libraries/Errors.sol";

contract Elector is IElector {

    // EVENTS
    event electionIsOverEvent();
    event oneUSDCostCalculatedEvent(uint128 oneUSDCost);

    // ENUMS
    enum Status {
        electionIsInProgress,
        validation,
        revealingMode,
        waitingForFinalQuotationCalculation,
        validationIsOver
    }

    // STATUS
    Status public status;
    uint revealingStartTime;

    // DATA (election)
    mapping(address => uint128) validatorsStake;

    // DATA (regular validation)
    uint256 random;
    uint lastNow;
    mapping(address => uint128) public validatorsRank;
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
    TvmCell validatorsCode;

    // COSTS AND BALANCES
    uint128 constant SLASH_COST = 1 ton;
    // max balance at which the commission is charged
    uint128 constant MIN_BALANCE = 10 ton;
    uint128 constant SET_QUOTATION_COMISSION = 0.3 ton;
    uint128 constant MIN_STAKE_SIZE = 10 kiloton; // КОСТЫЛЬ!

    // OTHER CONSTANTS
    uint constant REVEAL_FREQUENCY_FACTOR = 20;
    uint constant REVEALING_MODE_DURATION = 5;
    uint constant QUOTATION_LIFETIME = 3;
    uint constant NUMBER_OF_CHECKS_BEFORE_BAN = 3;

    // METHODS
    constructor(
        uint signUpStageBeginningArg,
        uint signUpStageDurationArg,
        uint validationStageBeginningArg,
        uint validationStageDurationArg,
        TvmCell validatorsCodeArg
    ) public {
        require(tvm.pubkey() != 0, Errors.NO_PUB_KEY);
        require(tvm.pubkey() == msg.pubkey(), Errors.WRONG_PUB_KEY);
        tvm.accept();

        signUpStageBeginning = signUpStageBeginningArg;
        signUpStageDuration = signUpStageDurationArg;
        validationStageBeginning = validationStageBeginningArg;
        validationStageDuration = validationStageDurationArg;
        validatorsCode = validatorsCodeArg;
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
        require(
            addressFitsValidatorsCode(msg.sender, msg.pubkey()),
            Errors.VALIDATOR_HAS_INCORRECT_ADDRESS
        );

        validatorsStake[msg.sender] = stakeSize;
    }

    function endElection() override external {
        require(now > signUpStageBeginning + signUpStageDuration, Errors.WRONG_MOMENT);
        require(status == Status.electionIsInProgress);
        tvm.accept();

        for ((address validator, uint stakeSize) : validatorsStake) {
            // TODO algorithm should be different!!!!
            if (stakeSize >= MIN_STAKE_SIZE) {
                validatorsRank[validator] = 0;
            }
        }

        emit electionIsOverEvent();
        status = Status.validation;
    }

    // VALIDATION PHASE
    function setQuotation(
        uint256 hashedQuotation
    ) override external takeComissionAndTransferRemainingValueBack {
        require(validatorsRank.exists(msg.sender), Errors.WRONG_SENDER);

        lastQuotationHash[msg.sender] = hashedQuotation;
        lastQuotationTime[msg.sender] = now;

        TvmBuilder builder;
        builder.store(random, hashedQuotation);
        random = tvm.hash(builder.toCell());

        if (status == Status.revealingMode) {
            if ((now - revealingStartTime) > REVEALING_MODE_DURATION) {
                status = Status.waitingForFinalQuotationCalculation;
                Elector(this).calcFinalQuotation();
            }
            if (quotationsToReveal.exists(msg.sender)) {
                // TODO it drains balance...
                // TODO dont call extra times
                IValidator(msg.sender).requestRevealing(
                    quotationsToReveal[msg.sender]
                );
            }
        }

        if (now != lastNow) {
            if (((random % REVEAL_FREQUENCY_FACTOR) == 0) && (status == Status.validation)) {
                turnOnRevealingMode();
            }
        }

        lastNow = now;
    }

    function revealQuotation(
        uint128 oneUSDCost,
        uint256 salt
    ) override external transferRemainingValueBack {
        require(validatorsRank.exists(msg.sender), Errors.WRONG_SENDER);
        require(status == Status.revealingMode, Errors.NOT_REVEALING_MODE);
        require(quotationsToReveal.exists(msg.sender), Errors.NOTHING_TO_REVEAL);

        uint256 quotationHash = quotationsToReveal[msg.sender];
        require(
            saltedCostHash(oneUSDCost, salt) == quotationHash,
            Errors.INCORRECT_REVEAL_DATA
        );

        revealedQuotations[msg.sender] = oneUSDCost;
        delete quotationsToReveal[msg.sender];
    }


    struct Quotation {address validator; uint128 value;}

    function calcFinalQuotation() override external {
        require(msg.sender == address(this), Errors.WRONG_SENDER);
        require(status == Status.waitingForFinalQuotationCalculation, Errors.NOT_REVEALING_MODE);
        tvm.accept();

        Quotation[] quotations = sortedQuotations();
        uint n = quotations.length;

        // TODO can be calculated with k-th statistic algo
        uint128 v_0 = quotations[0].value;
        uint128 v_25 = quotations[(n - 1) / 4].value;
        uint128 v_50 = quotations[n / 2].value;
        uint128 v_75 = quotations[(3 * (n - 1)) / 4].value;
        uint128 v_100 = quotations[n - 1].value;

        for (uint i = 0; i < n; i++) {
            uint128 P; // P=10^9 means probability=1
            Quotation quotation = quotations[i];
            if (quotation.value < v_25) {
                P = (quotation.value - v_0) * 1000000000 / v_25;
            } else if (quotation.value > v_75) {
                P = (v_100 - quotation.value) * 1000000000 / (v_100 - v_75);
            } else {
                P = 1000000000;
            }

            uint128 r = validatorsRank[quotation.validator];
            uint128 r_c = 1000000000 - P;

            // here constant a = 2/7
            uint128 r_new = (5*r / 7) + (2*r_c / 7);
            if (r_new >= 500000000) {
                uint badChecks = badChecksInARow[quotation.validator];
                if (badChecks + 1 == NUMBER_OF_CHECKS_BEFORE_BAN) {
                    IValidator(quotation.validator).slash();
                    delete validatorsRank[quotation.validator];
                    delete revealedQuotations[quotation.validator];
                } else {
                    badChecksInARow[quotation.validator] += 1;
                    validatorsRank[quotation.validator] = r_new;
                }
            } else {
                validatorsRank[quotation.validator] = r_new;
                delete badChecksInARow[quotation.validator];
            }
        }

        for ((address validator,) : quotationsToReveal) {
            uint128 r = validatorsRank[validator];
            uint128 r_c = 1000000000;

            // here constant a = 2/7
            uint128 r_new = (5*r / 7) + (2*r_c / 7);
            if (r_new >= 500000000) {
                uint badChecks = badChecksInARow[validator];
                if (badChecks + 1 == NUMBER_OF_CHECKS_BEFORE_BAN) {
                    IValidator(validator).slash();
                    delete validatorsRank[validator];
                    delete revealedQuotations[validator];
                } else {
                    badChecksInARow[validator] += 1;
                    validatorsRank[validator] = r_new;
                }
            } else {
                validatorsRank[validator] = r_new;
                delete badChecksInARow[validator];
            }
        }

        emit oneUSDCostCalculatedEvent(v_50);
        status = Status.validation;
        // TODO send necessery data to NOT-Bank
    }

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) override external {
        // TODO check (msg.sender == owner) or something like that...
        require(tvm.pubkey() == msg.pubkey(), Errors.WRONG_PUB_KEY);
        require(now > validationStageBeginning + validationStageDuration);
        tvm.accept();

        selfdestruct(destination);
    }

    // INLINES
    function addressFitsValidatorsCode(
        address _address,
        uint256 pubkey
    ) private inline returns (bool) {
        return true;
    }

    function turnOnRevealingMode() inline private {
        mapping(address => uint256) tempQuotationsToReveal;
        for ((address validator, uint time) : lastQuotationTime) {
            if (now - time <= QUOTATION_LIFETIME) {
                tempQuotationsToReveal[validator] = lastQuotationHash[validator];
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

    function sortedQuotations() inline private returns (Quotation[] res) {
        for ((address validator, uint128 value) : revealedQuotations) {
            res.push(Quotation(validator, value));
        }

        uint n = res.length;
        Quotation temp;
        for (uint i = 1; i < n; i++) {
            for (uint j = 0; j < i; j++) {
                if (res[i].value < res[j].value) {
                    temp = res[i];
                    res[i] = res[j];
                    res[j] = temp;
                }
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
