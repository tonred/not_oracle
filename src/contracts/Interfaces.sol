/* solhint-disable */
pragma ton-solidity >= 0.35.0;
pragma AbiHeader expire;
pragma AbiHeader time;

interface IElector {
    // ELECTION PHASE
    function signUp(
        uint128 stakeSize,
        uint validationStartTime,
        uint validationDuration
    ) external;
    function endElection() external;

    // VALIDATION PHASE
    function setQuotation(uint256 hashedQuotation) external;
    function revealQuotation(uint128 oneUSDCost, uint256 salt) external;

    // has to be called by contract itself on last revealQuotation call
    function calcFinalQuotation() external;

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) external;
}

interface IValidator {
    // ELECTION PHASE
    function onStakeTransfered(uint128 stakeSizeArg) external;
    function signUp() external;

    // VALIDATION PHASE
    function setQuotation(uint256 hashedQuotation) external;
    function requestRevealing(uint256 hashedQuotation) external;
    function revealQuotation(uint128 oneUSDCost, uint256 salt, uint256 hashedQuotation) external;
    function slash() external;

    // AFTER VALIDATION PHASE
    function cleanUp(address destination) external;
}
