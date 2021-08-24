# NOT-oracle
## Abstract
The main goal of the project is to make reliable, trustful and decentralized system providing the stream of TON/USD quotations to the blockchain. This process called NOT-validation. It's an analog of real validation, but it makes not the chain of blocks, but the sequence of quotations.

## Informal description
This software consists of three parts:
* NOT-Validator (off-chain). It's server-side software which asks some exchange for the quotations and sends it to the blockchain.
* NOT-Validator (smart contract). Proxy contract representing NOT-Validator in the blockchain.
* NOT-Elector. Contract collecting data from NOT-Validators and calculating final quotations (NOT-Blocks).

Here we use the same proof-of-stake mechanics as real Validation. Each NOT-Validator has to transfer DePool stake to itself and it can be slashed by NOT-Elector in case of malicious.

NOT-Validation lifecycle consists of two parts:
* Sign-up (election) stage. Here NOT-Validators should deploy their proxy contracts, transfer stakes to it and sign-up in NOT-Elector. Afterall the NOT-Elector performs an "election" and choose validators to take part in a next stage.
* Validation stage. Here NOT-Validators provide quotations.

## Sign-up stage
Kind of obvious. The only controversial point is how to finalize the process of the election. Elector has `.endElection()` method. It can be called by anyone who wants. But only once and only in time.

## Validation stage
It's more sophisticated. Here we have kind two separate processes.

**NOT-Validators main loop**

1. Off-chain not-validator asks the exchange for a quotation.
2. Off-chain not-validator generate random salt, calculates `hash(quotation, salt)` and sends it to the NOT-Elector through the proxy contract.

The NOT-Elector can be in two modes. `validation` and `revealing`. (In the real code there are more then two modes, but others are technical and not such important).

**When the NOT-Elector receives the quotation, it should do the following steps:**

1. Save received quotation.
2. If in the revealing mode, ask caller to reveal it's last quotation was made before revealing mode.
3. If in the revealing mode, check if it has to be over. In such case ask itself to `.calcFinalQuotation()`.
4. If not in the revealing mode, toss the coin and check if it has to turn on the revealing mode.

**off-chain NOT-Validator** every second (time can be tuned) starts the following asynchronous tasks:

1. Ask exchange for the quotation and send it to NOT-Validator smart-contract (proxy-contract).
2. Process events emitted by proxy-contract. If `event RevealPlz(uint256 hashedQuotation)` is received, sends salt and quotation to the Elector (through the proxy contract, as usual).
