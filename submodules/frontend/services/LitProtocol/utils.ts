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

// Hardcoded secret name for Lit Protocol secrets
const LIT_PROTOCOL_SECRET_NAME = "LitProtocolPaymentDelegationSecrets";

// Get secrets from AWS Secrets Manager
const secretsManager = new SecretsManager({
  region: process.env.AWS_REGION || "us-west-1",
});

const getSecrets = async () => {
  const response = await secretsManager.getSecretValue({
    SecretId: LIT_PROTOCOL_SECRET_NAME,
  });
  const secrets = JSON.parse(response.SecretString || "{}");
  return {
    LIT_RELAYER_API_KEY: secrets.LIT_RELAYER_API_KEY,
    LIT_PAYER_SECRET_KEY: secrets.LIT_PAYER_SECRET_KEY,
  };
};

let LIT_RELAYER_API_KEY: string;
let LIT_PAYER_SECRET_KEY: string;

// Initialize secrets
getSecrets().then((secrets) => {
  LIT_RELAYER_API_KEY = secrets.LIT_RELAYER_API_KEY;
  LIT_PAYER_SECRET_KEY = secrets.LIT_PAYER_SECRET_KEY;
});

// Choose network based on environment
const getLitNetwork = () => {
  // Check if we're in production
  if (process.env.NODE_ENV === "production") {
    return LIT_NETWORK.Datil; // Use production network
  } else {
    return LIT_NETWORK.DatilDev; // Use development network for non-production
  }
};

// Get the appropriate relayer URL based on network
const getRelayerUrl = (endpoint: string) => {
  // Payment Delegation Database is only supported on datil and datil-test networks
  // Even in dev environment, we need to use datil-test for the relayer
  const network =
    process.env.NODE_ENV === "production" ? "datil" : "datil-test";
  return `https://${network}-relayer.getlit.dev/${endpoint}`;
};

const gatewayAddress = "https://gateway.irys.xyz/";

const getIrysUploader = async () => {
  const provider = new ethers.BrowserProvider(window.ethereum);
  const irysUploader = await WebUploader(WebEthereum).withAdapter(
    EthersV6Adapter(provider)
  );
  return irysUploader;
};

// Initialize the Lit client immediately
let litClientInitialized = false;
const litClient = new LitNodeClient({
  litNetwork: getLitNetwork(),
});

// Connect to Lit network automatically
(async () => {
  try {
    await litClient.connect();
    litClientInitialized = true;
    console.log("Lit client connected automatically");
  } catch (error) {
    console.error("Error connecting to Lit network:", error);
  }
})();

// Ensure Lit client is connected before operations
const ensureLitClientConnected = async () => {
  if (!litClientInitialized) {
    await litClient.connect();
    litClientInitialized = true;
  }
};

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
 * Register a new payer wallet with the Payment Delegation Database
 */
export const registerPayer = async (): Promise<{
  payerWalletAddress: string;
  payerSecretKey: string;
}> => {
  const headers = {
    "api-key": LIT_RELAYER_API_KEY,
    "Content-Type": "application/json",
  };

  try {
    console.log("🔄 Registering new payer...");
    const response = await fetch(getRelayerUrl("register-payer"), {
      method: "POST",
      headers: headers,
    });

    if (!response.ok) {
      throw new Error(`Error: ${await response.text()}`);
    }

    const data = await response.json();
    console.log(`✅ New payer registered: ${data.payerWalletAddress}`);

    return {
      payerWalletAddress: data.payerWalletAddress,
      payerSecretKey: data.payerSecretKey,
    };
  } catch (error) {
    console.error("Error registering payer:", error);
    throw error;
  }
};

/**
 * Add users as payees for the payer wallet
 */
export const addUsers = async (users: string[]): Promise<boolean> => {
  const headers = {
    "api-key": LIT_RELAYER_API_KEY,
    "payer-secret-key": LIT_PAYER_SECRET_KEY,
    "Content-Type": "application/json",
  };

  try {
    console.log(`🔄 Adding ${users.length} users as delegatees...`);
    const response = await fetch(getRelayerUrl("add-users"), {
      method: "POST",
      headers: headers,
      body: JSON.stringify(users),
    });

    if (!response.ok) {
      throw new Error(`Error: ${await response.text()}`);
    }

    const data = await response.json();
    if (data.success !== true) {
      throw new Error(`Error: ${data.error}`);
    }
    console.log("✅ Added users as delegatees");

    return true;
  } catch (error) {
    console.error("Error adding users:", error);
    throw error;
  }
};

/**
 * Adds the current user to the Payment Delegation Database
 */
export const addCurrentUserAsDelegatee = async (): Promise<boolean> => {
  // Get the user's address from browser ethereum provider
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const userWalletAddress = await signer.getAddress();

  console.log(
    `Adding current user (${userWalletAddress}) to payment delegation database`
  );

  return await addUsers([userWalletAddress]);
};

export const encryptSecret = async (
  text: string
): Promise<{ ciphertext: string; dataToEncryptHash: string }> => {
  await ensureLitClientConnected();

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
    ciphertext: cipherText,
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

  await ensureLitClientConnected();

  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const walletAddress = await signer.getAddress();

  const latestBlockhash = await litClient.getLatestBlockhash();

  // Get session signatures without capacity delegation since it's handled by the Payment Delegation Database
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
    // No need to include capacityDelegationAuthSig anymore
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

// Make sure a specific wallet address is registered in the payment delegation system
export const ensureUserIsRegistered = async (
  address: string
): Promise<boolean> => {
  try {
    // First ensure we have the required secrets
    if (!LIT_RELAYER_API_KEY || !LIT_PAYER_SECRET_KEY) {
      const secrets = await getSecrets();
      LIT_RELAYER_API_KEY = secrets.LIT_RELAYER_API_KEY;
      LIT_PAYER_SECRET_KEY = secrets.LIT_PAYER_SECRET_KEY;

      // If we don't have a payer secret key, we need to register a new payer
      if (!LIT_PAYER_SECRET_KEY) {
        const { payerSecretKey } = await registerPayer();
        LIT_PAYER_SECRET_KEY = payerSecretKey;

        // Here you would need to save this to your secrets manager
        console.log(
          "⚠️ New payer registered. Save the payerSecretKey securely!"
        );
        console.log(
          "You need to save this secret key to your secrets manager."
        );
      }
    }

    // Add the user to the payment delegation database
    return await addUsers([address]);
  } catch (error) {
    console.error("Error ensuring user is registered:", error);
    throw error;
  }
};
