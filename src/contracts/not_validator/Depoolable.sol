/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";

abstract contract Depoolable is IDepoolable {

    uint32 constant ERROR_DEPOOL_NOT_REGISTERED = 131;
    uint32 constant ERROR_DEPOOL_NOT_ENOUGH_VALUE = 132;
    uint32 constant ERROR_DEPOOL_NOT_ACTIVE = 133;
    uint32 constant ERROR_DEPOOL_NOT_AUTHORIZED = 134;
    uint32 constant ERROR_DEPOOL_NOT_INITIZALIZED = 135;
    uint32 constant ERROR_DEPOOL_ALREADY_INITIZALIZED = 136;

    mapping (address => bool) public depools;

    address public activeDepool;
    bool public ended;
    bool public terminationStarted;
    uint128 public amountDeposited;
    uint128 public amountToSendExternally;
    address public depooledParticipant;
    address public owner;

    function init(
        mapping (address => bool) _depools,
        address _owner
    ) inline internal {
        depools = _depools;
        owner = _owner;
    }

    function onTransfer(address source, uint128 amount_) override external {
        require(depools.exists(msg.sender), ERROR_DEPOOL_NOT_REGISTERED);
        require(activeDepool == address(0) || activeDepool == msg.sender, ERROR_DEPOOL_NOT_ACTIVE);
        tvm.accept();
        activeDepool = msg.sender;
        depooledParticipant = source;
        amountDeposited = amount_;
    }

    function onRoundComplete(
        uint64 roundId,
        uint64 reward,
        uint64 ordinaryStake,
        uint64 vestingStake,
        uint64 lockStake,
        bool reinvest,
        uint8 reason
    ) override external {
        require(msg.sender == activeDepool, ERROR_DEPOOL_NOT_ACTIVE);
        tvm.accept();

        IDePool(msg.sender).transferStake(depooledParticipant, ordinaryStake);
        selfdestruct(owner);
    }
}