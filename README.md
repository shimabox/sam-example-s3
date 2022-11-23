# sam-example-s3

[AWS Lambda実践ガイド 第2版](https://www.amazon.co.jp//dp/4295013307 "AWS Lambda実践ガイド 第2版 (impress top gear) | 大澤 文孝 |本 | 通販 | Amazon") 第5章の写経です。  
※ 厳密には、5-7までです

## 前提条件

### 0. ツール

- [Docker](https://docs.docker.jp/desktop/toc.html "Docker Desktop — Docker-docs-ja 20.10 ドキュメント")
- [AWS CLI](https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/getting-started-install.html "AWS CLI の最新バージョンをインストールまたは更新します。 - AWS Command Line Interface")
- [AWS SAM CLI](https://docs.aws.amazon.com/ja_jp/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html "AWS SAM CLI のインストール - AWS Serverless Application Model")

はインストール済みとします。

### 1. Lambda開発者アカウントが作成されている

- 本書の**Appendix A**にて、Lambda開発者アカウントの作成 が完了している
- Lambda開発者アカウントのAWS CLIオプションの設定が完了している
  - `aws configure` で設定しておいてください
  - CLI で実行するためです
  - Cloud9 は使いません

### 2. Lambda実行ロールが作成されている

- 本書の**Appendix B**にて、Lambda実行ロールの作成 が完了している
  - `example-lambda-role` というIAMロールが存在している

### 3. S3バケットが作成されている

- **5-2 S3バケットの作成とアクセス権の設定** が完了している
  - 配置用バケット
    - 本書だと、`exampleread00001234`
    - ※ 適宜バケット名を修正してください
  - 出力用バケット
    - 本書だと、`examplewrite00001234`
    - ※ 適宜バケット名を修正してください

## 環境構築に必要となる値を環境変数に設定

※ 説明を簡単にするため環境変数に設定しますが、その後のコマンドでそれぞれ利用すればいいので必ずしも設定する必要はありません

### LambdaロールのARN

```sh
$ aws iam list-roles --query "Roles[?RoleName=='example-lambda-role'].Arn"
```
と打つと
```js
[
  "arn:aws:iam::xxxxxxxxxxxx:role/example-lambda-role"
]
```
が出力されるので、`arn:aws:iam::xxxxxxxxxxxx:role/example-lambda-role` をコピーして環境変数に設定します。
```sh
$ LAMBDA_ROLE_ARN={上記でコピーした値}
```

※ [jq](https://stedolan.github.io/jq/download/ "Download jq") が使える場合
```
$ LAMBDA_ROLE_ARN=`aws iam list-roles \
    --query "Roles[?RoleName=='example-lambda-role'].Arn" \
    | jq -r '.[]'`
```

### 配置用S3バケット名

```sh
$ INPUT_S3_BUCKET={前提条件 3. S3バケットが作成されている で作成した配置用バケット名}
```

### 出力用S3バケット名

```sh
$ OUTPUT_S3_BUCKET={前提条件 3. S3バケットが作成されている で作成した出力用バケット名}
```

以下でそれぞれ値が出力されればOKです。
```sh
echo $LAMBDA_ROLE_ARN
echo $INPUT_S3_BUCKET
echo $OUTPUT_S3_BUCKET
```

## Clone

```
$ git clone https://github.com/shimabox/sam-example-s3.git
$ cd sam-example-s3
```

## ビルド

```sh
$ sam build -u
```

## デプロイ

```sh
$ sam deploy -g \
    --parameter-overrides \
      LambdaRoleArn="${LAMBDA_ROLE_ARN}" \
      InputBucket="${INPUT_S3_BUCKET}" \
      OutputBucket="${OUTPUT_S3_BUCKET}"
```
以下のように聞かれるので適宜ッタターンします。
```sh
Setting default arguments for 'sam deploy'
  =========================================
  Stack Name [sam-app]: stack-sam-example-s3 # 適宜修正しても大丈夫だと思います
  AWS Region [ap-northeast-1]: Enter
  Parameter LambdaRoleArn [{LambdaロールのARN}]: Enter
  Parameter InputBucket [{配置用S3バケット名}]: Enter
  Parameter OutputBucket [{出力用S3バケット名}]: Enter
  #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
  Confirm changes before deploy [y/N]: y
  #SAM needs permission to be able to create roles to connect to the resources in your template
  Allow SAM CLI IAM role creation [Y/n]: n
  Capabilities [['CAPABILITY_IAM']]: Enter
  #Preserves the state of previously provisioned resources when an operation fails
  Disable rollback [y/N]: Enter
  Save arguments to configuration file [Y/n]: Enter
  SAM configuration file [samconfig.toml]: Enter
  SAM configuration environment [default]: Enter
  ~
  Previewing CloudFormation changeset before deployment
  ======================================================
  Deploy this changeset? [y/N]: y
  ~
```

`Successfully created/updated stack - stack-sam-example-s3 in ap-northeast-1` が出ればOKです。

### デプロイで失敗する場合:innocent:

```sh
Error: Unable to upload artifact HelloWorldFunction referenced by CodeUri parameter of HelloWorldFunction resource.

S3 Bucket does not exist.
```

こんなエラーが出る場合、CloudFormationのスタックに`aws-sam-cli-managed-default`があったら削除すると上手くいくかもしれません。  
※ 自分の場合、先に試行錯誤を色々としていた状態が残っていて？うまくいかなかったようなのですが、思い切って消したらデプロイできました  
※ 詳しい理由は分かりません...

## S3バケットをイベントソースとして設定

配置用S3バケットへのPUTイベントをトリガーに設定します。  
※ 本書の通り、`s3:ObjectCreated:*` をイベントに設定していますが、`s3:ObjectCreated:Put` でもいいと思います

### Lambda関数名を取得

```sh
$ FUNC=`aws cloudformation describe-stacks \
    --stack-name "stack-sam-example-s3" \
    --query "Stacks[0].Outputs[?OutputKey=='MyFunctionArn'].OutputValue" \
    --output text`
```

### 設定

```sh
$ aws s3api put-bucket-notification-configuration \
    --bucket "${INPUT_S3_BUCKET}" \
    --notification-configuration \
      "{\"LambdaFunctionConfigurations\": \
      [{\"LambdaFunctionArn\":\"${FUNC}\", \
      \"Events\": [\"s3:ObjectCreated:*\"]}]}"
```

## 確認

配置用S3バケットに適当なファイルをアップロードして、出力用S3バケットにzipが出力されていればOKです:+1:

## 参考

- [AWS Lambdaで使いたい環境変数をAWS SAM CLIでどうするか - Qiita](https://qiita.com/c3drive/items/9c1ed0686dc3aec88935 "AWS Lambdaで使いたい環境変数をAWS SAM CLIでどうするか - Qiita")
  - ARNの値は隠したほうがいいのかなぁと思い参考にしました
  - `--parameter-overrides` で環境変数を渡せます
