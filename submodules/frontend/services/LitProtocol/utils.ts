import { WebUploader } from "@irys/web-upload";
import { WebEthereum } from "@irys/web-upload-ethereum";
import { EthersV6Adapter } from "@irys/web-upload-ethereum-ethers-v6";
import { ethers } from "ethers";
import { LitNodeClient } from "@lit-protocol/lit-node-client";
import { encryptString, decryptToString } from "@lit-protocol/encryption";
import { LIT_NETWORK, LIT_ABILITY } from "@lit-protocol/constants";
import {
  LitAccessControlConditionResource,
  createSiweMessage,
  generateAuthSig,
} from "@lit-protocol/auth-helpers";
import { SecretsManager } from "@aws-sdk/client-secrets-manager";

// Get secrets from AWS Secrets Manager
const secretsManager = new SecretsManager({
  region: process.env.AWS_REGION || "us-west-1",
});

const getSecrets = async () => {
  const response = await secretsManager.getSecretValue({
    SecretId: process.env.LIT_PROTOCOL_SECRET_NAME,
  });
  const secrets = JSON.parse(response.SecretString || "{}");
  return {
    CAPACITY_CREDIT_TOKEN_ID: secrets.CAPACITY_CREDIT_TOKEN_ID,
    CREDIT_OWNER_PRIVATE_KEY: secrets.CREDIT_OWNER_PRIVATE_KEY,
  };
};

let CAPACITY_CREDIT_TOKEN_ID: string;
let CREDIT_OWNER_PRIVATE_KEY: string;

// Initialize secrets
getSecrets().then((secrets) => {
  CAPACITY_CREDIT_TOKEN_ID = secrets.CAPACITY_CREDIT_TOKEN_ID;
  CREDIT_OWNER_PRIVATE_KEY = secrets.CREDIT_OWNER_PRIVATE_KEY;
});

// Choose network based on environment
const getLitNetwork = () => {
  // Check if we're in production
  if (process.env.NODE_ENV === "production") {
    return LIT_NETWORK.Datil; // Use production network (Manzano)
  } else {
    return LIT_NETWORK.DatilDev; // Use dev network otherwise
  }
};

const gatewayAddress = "https://gateway.irys.xyz/";

const getIrysUploader = async () => {
  const provider = new ethers.BrowserProvider(window.ethereum);
  const irysUploader = await WebUploader(WebEthereum).withAdapter(
    EthersV6Adapter(provider)
  );
  return irysUploader;
};

const litClient = new LitNodeClient({
  litNetwork: getLitNetwork(),
});

const getAccessControlConditions = () => {
  return [
    {
      conditionType: "evmBasic" as const,
      contractAddress: "" as const,
      standardContractType: "" as const,
      chain: "ethereum" as const,
      method: "eth_getBalance" as const,
      parameters: [":userAddress", "latest"],
      returnValueTest: {
        comparator: ">=" as const,
        value: "10000000000000", // 0.00001 ETH
      },
    },
  ];
};

/**
 * Creates capacity delegation auth signature for the current user
 */
export const createCapacityDelegation = async (): Promise<any> => {
  // Initialize the Lit client
  const localLitClient = new LitNodeClient({
    litNetwork: getLitNetwork(),
    checkNodeAttestation: true,
  });

  await localLitClient.connect();

  // Create wallet instance for the credit owner using the hardcoded private key
  const creditOwnerWallet = new ethers.Wallet(CREDIT_OWNER_PRIVATE_KEY);

  // Get the user's address from browser ethereum provider
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const userWalletAddress = await signer.getAddress();

  console.log(
    `Creating capacity delegation from owner to current user: ${userWalletAddress}`
  );

  // Create the capacity delegation auth signature
  const { capacityDelegationAuthSig } =
    await localLitClient.createCapacityDelegationAuthSig({
      uses: "100", // Number of uses for this delegation
      dAppOwnerWallet: creditOwnerWallet,
      capacityTokenId: CAPACITY_CREDIT_TOKEN_ID,
      delegateeAddresses: [userWalletAddress], // Delegate to the current user
    });

  console.log("Capacity delegation created successfully");
  return capacityDelegationAuthSig;
};

export const encryptSecret = async (
  text: string
): Promise<{ ciphertext: string; dataToEncryptHash: string }> => {
  await litClient.connect();

  const { ciphertext, dataToEncryptHash } = await encryptString(
    {
      accessControlConditions: getAccessControlConditions(),
      dataToEncrypt: text,
    },
    litClient
  );

  return { ciphertext, dataToEncryptHash };
};

export const uploadToIrys = async (
  cipherText: string,
  dataToEncryptHash: string
): Promise<string> => {
  const irysUploader = await getIrysUploader();

  const dataToUpload = {
    ciphertext: cipherText, // Note: using ciphertext (lowercase) consistently
    dataToEncryptHash: dataToEncryptHash,
    accessControlConditions: getAccessControlConditions(),
  };

  try {
    const tags = [{ name: "Content-Type", value: "application/json" }];
    const receipt = await irysUploader.upload(JSON.stringify(dataToUpload), {
      tags,
    });
    return receipt?.id ? `${gatewayAddress}${receipt.id}` : "";
  } catch (error) {
    console.error("Error uploading data: ", error);
    throw error;
  }
};

export const downloadFromIrys = async (
  id: string
): Promise<[string, string, any[]]> => {
  const url = `${gatewayAddress}${id}`;
  console.log("Downloading from URL:", url);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Failed to retrieve data for ID: ${id}`);

    const data = await response.json();
    console.log("Raw data from Irys:", data);

    // Ensure consistent property names
    const ciphertext = data.ciphertext || data.cipherText;
    const dataToEncryptHash = data.dataToEncryptHash;
    const accessControlConditions = data.accessControlConditions;

    if (!ciphertext || !dataToEncryptHash || !accessControlConditions) {
      console.error("Missing required data from Irys:", {
        ciphertext,
        dataToEncryptHash,
        accessControlConditions,
      });
      throw new Error("Missing required data from Irys");
    }

    return [ciphertext, dataToEncryptHash, accessControlConditions];
  } catch (error) {
    console.error("Error retrieving data:", error);
    throw error;
  }
};

export const decryptData = async (
  encryptedText: string,
  dataToEncryptHash: string,
  accessControlConditions: any[]
): Promise<string> => {
  console.log("Decrypting with:", {
    encryptedText,
    dataToEncryptHash,
    accessControlConditions,
  });

  await litClient.connect();

  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const walletAddress = await signer.getAddress();

  const latestBlockhash = await litClient.getLatestBlockhash();

  // Get capacity delegation for the current user
  const capacityDelegationAuthSig = await createCapacityDelegation();

  // Get session signatures with capacity delegation
  const sessionSigs = await litClient.getSessionSigs({
    chain: "ethereum",
    expiration: new Date(Date.now() + 1000 * 60 * 10).toISOString(), // 10 minutes
    resourceAbilityRequests: [
      {
        resource: new LitAccessControlConditionResource("*"),
        ability: LIT_ABILITY.AccessControlConditionDecryption,
      },
    ],
    authNeededCallback: async ({
      uri,
      expiration,
      resourceAbilityRequests,
    }) => {
      const toSign = await createSiweMessage({
        uri,
        expiration,
        resources: resourceAbilityRequests,
        walletAddress: walletAddress,
        nonce: latestBlockhash,
        litNodeClient: litClient,
        domain: window.location.hostname,
      });

      return await generateAuthSig({
        signer: signer,
        toSign,
      });
    },
    capacityDelegationAuthSig, // Include capacity delegation
  });

  // Decrypt using sessionSigs
  try {
    const decryptedString = await decryptToString(
      {
        accessControlConditions,
        chain: "ethereum",
        ciphertext: encryptedText,
        dataToEncryptHash,
        sessionSigs,
      },
      litClient
    );

    return decryptedString;
  } catch (error) {
    console.error("Decryption error:", error);
    throw error;
  }
};
