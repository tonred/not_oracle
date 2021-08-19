/* solhint-disable */
pragma ton-solidity >= 0.45.0;
pragma AbiHeader expire;


contract Contract {
    constructor() public {
        tvm.accept();
    }

    function calc(uint128 value, uint256 salt) external pure returns (uint256 hash) {
        tvm.accept();
        TvmBuilder builder;
        builder.store(value, salt);
        hash = tvm.hash(builder.toCell());
    }
}
