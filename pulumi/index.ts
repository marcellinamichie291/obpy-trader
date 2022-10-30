import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";

// Create an AWS resource (S3 Bucket)
const bucket = new aws.s3.Bucket("obpy");

// Export the name of the bucket
export const bucketName = bucket.id;

const obpyHandlerRole = new aws.iam.Role("obpyHandlerRole", {
  assumeRolePolicy: {
    Version: "2012-10-17",
    Statement: [
      {
        Action: "sts:AssumeRole",
        Principal: {
          Service: "lambda.amazonaws.com",
        },
        Effect: "Allow",
        Sid: "",
      },
    ],
  },
});

const obpyHandlerFunc = new aws.lambda.Function("obpyHandlerFunc", {
  code: new pulumi.asset.AssetArchive({
    ".": new pulumi.asset.FileArchive("./app"),
  }),
  runtime: "python3.9",
  handler: "lambda_handler",
  role: obpyHandlerRole.arn,
});

bucket.onObjectCreated("obpyHandler", obpyHandlerFunc);
