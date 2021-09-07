/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;

interface INotElector {
    // ELECTION PHASE
    function signUp(
        uint128 stakeSize,
        uint validationStartTime,
        uint validationDuration
    ) external;
    function endElection() external;

    // VALIDATION PHASE
    function setQuotation(uint256 hashedQuotation) external;
    function revealQuotation(uint128 oneUSDCost) external;
    function quotationIsTooOld() external;

    // has to be called by contract itself on last revealQuotation call
    // function calcFinalQuotation() external;

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) external;
}

interface INotValidator {
    // ELECTION PHASE
    function signUp() external;

    // VALIDATION PHASE
    function setQuotation(uint256 hashedQuotation) external;
    function requestRevealing() external;
    function revealQuotation(uint128 oneUSDCost, uint256 salt) external;
    function slash() external;

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) external;
}

interface IDePool {
    function addOrdinaryStake(uint64 stake) external;
    function transferStake(address dest, uint64 amount) external;
    function withdrawAll() external;
}

interface IDepoolable {
    function onRoundComplete(
        uint64 roundId,
        uint64 reward,
        uint64 ordinaryStake,
        uint64 vestingStake,
        uint64 lockStake,
        bool reinvest,
        uint8 reason
    ) external;
    function onTransfer(address source, uint128 amount_) external;
}