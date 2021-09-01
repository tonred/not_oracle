/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;
pragma AbiHeader time;
pragma AbiHeader pubkey;

import "../Interfaces.sol";
import "../libraries/Errors.sol";

contract DePoolMock is IDePool {

    constructor() public {
        tvm.accept();
    }

    function transferStake(address dest, uint64 amount) override external {
        tvm.accept();
        IDepoolable(dest).onTransfer(address(100500), amount);
    }

    function cleanUp(address destination) external {
        tvm.accept();

        selfdestruct(destination);
    }

    function addOrdinaryStake(uint64 stake) override external {}
    function withdrawAll() override external {}
}