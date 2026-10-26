/**
 * Measure gas used by ModelProvenance registerModel / registerVersion / verifyModel.
 * Prints measured values only — never fabricated estimates.
 *
 * Usage: npx hardhat run scripts/measure_gas.js
 */
const hre = require("hardhat");

async function main() {
  const [owner, creator] = await hre.ethers.getSigners();
  const Factory = await hre.ethers.getContractFactory("ModelProvenance");
  const registry = await Factory.deploy(owner.address);
  await registry.waitForDeployment();

  const modelId = hre.ethers.id("gas-root");
  const modelHash = hre.ethers.id("gas-hash-root");
  const metadataHash = hre.ethers.id("gas-meta-root");

  const registerTx = await registry
    .connect(creator)
    .registerModel(modelId, modelHash, metadataHash);
  const registerReceipt = await registerTx.wait();

  const childId = hre.ethers.id("gas-child");
  const childHash = hre.ethers.id("gas-hash-child");
  const childMeta = hre.ethers.id("gas-meta-child");
  const versionTx = await registry
    .connect(creator)
    .registerVersion(childId, childHash, childMeta, modelId, 2);
  const versionReceipt = await versionTx.wait();

  // verifyModel is view — report intrinsic gas via estimateGas
  const verifyGas = await registry.connect(creator).verifyModel.estimateGas(modelId, modelHash);

  const result = {
    network: "hardhat",
    chainId: Number((await hre.ethers.provider.getNetwork()).chainId),
    measuredAt: new Date().toISOString(),
    deployAddress: await registry.getAddress(),
    gas: {
      registerModel: Number(registerReceipt.gasUsed),
      registerVersion: Number(versionReceipt.gasUsed),
      verifyModelEstimate: Number(verifyGas),
    },
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
