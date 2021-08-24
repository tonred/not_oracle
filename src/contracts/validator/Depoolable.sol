/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";

abstract contract Depoolable is IDepoolable {

    // uint64 constant MIN_BID_BALANCE = 5 ton;

    uint32 constant ERROR_DEPOOL_NOT_REGISTERED = 131;
    uint32 constant ERROR_DEPOOL_NOT_ENOUGH_VALUE = 132;
    uint32 constant ERROR_DEPOOL_NOT_ACTIVE = 133;
    uint32 constant ERROR_DEPOOL_NOT_AUTHORIZED = 134;
    uint32 constant ERROR_DEPOOL_NOT_INITIZALIZED = 135;
    uint32 constant ERROR_DEPOOL_ALREADY_INITIZALIZED = 136;

    mapping (address => bool) public depools;

    address public activeDepool;
    // bool public initialized;
    bool public ended;
    bool public terminationStarted;
    uint128 public amountDeposited;
    uint128 public amountToSendExternally;
    address public depooledParticipant;
    // address public dest;
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
        require(depools.exists(msg.sender), ERROR_DEPOOL_NOT_REGISTERED);
        tvm.accept();

        if(terminationStarted){
            delete depools[msg.sender];
            if(depools.empty()) {
                selfdestruct(owner);
            }
        }
        else if(ended && msg.sender == activeDepool) {
            uint128 realAmountToSend = math.min(msg.value, amountToSendExternally);
            if(realAmountToSend > 0) {
                owner.transfer(realAmountToSend, false, 1);
            }
            IDePool(msg.sender).transferStake(depooledParticipant, ordinaryStake);
        }
    }
}