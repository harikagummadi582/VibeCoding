# AWS Profile and Version Checking Guidelines

## AWS CLI Profile

Always use the AWS CLI profile "kiro-eks-workshop" for all AWS commands in this workspace.

When running AWS CLI commands, include the `--profile kiro-eks-workshop` flag:

- `aws s3 ls --profile kiro-eks-workshop`
- `aws eks list-clusters --profile kiro-eks-workshop`
- `aws iam get-user --profile kiro-eks-workshop`

## Version Checking

When checking for specific versions of packages or tools:

1. First try the standard `version` command
2. If that doesn't return anything, use the `--version` flag instead
3. Common patterns:
   - `kubectl version` or `kubectl --version`
   - `aws --version`
   - `docker version` or `docker --version`
   - `node --version`
   - `npm --version`

This ensures consistent AWS profile usage and reliable version checking across all operations in this workspace.
