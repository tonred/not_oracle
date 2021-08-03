/* solhint-disable */
pragma ton-solidity >= 0.35.0;
pragma AbiHeader expire;
pragma AbiHeader time;

interface IElector {
    // ELECTION PHASE
    function signUp() external;
    function elect() external; // ends election

    // VALIDATION PHASE
    function revealQuotationMoment(uint moment, uint256 salt) external;
    function setValidatorsQuotation(uint128 oneUSDCost) external;
}

interface IValidator {
    // ELECTION PHASE
    function onStakeTransfered(???) external;
    function signUp(IElector elector) external;

    // VALIDATION PHASE
    function setQuotation() external;
    function slash() external;

    // AFTER VALIDATION PHASE
    function cleanUp() external;
}
