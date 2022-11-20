import boto3
import tempfile
import os
import pyminizip

def lambda_handler (event, context):
    # S3にアクセスするためのオブジェクトを取得
    s3 = boto3.resource('s3')
    tmpdir = tempfile.TemporaryDirectory()
    for rec in event ['Records']:
        filename = rec['s3']['object']['key']
        bucketname = rec['s3']['bucket']['name']

        # ファイルにアクセスするためのオブジェクトを取得
        obj = s3.Object (bucketname, filename)

        # ファイルの情報を取得
        response = obj.get()

        # 一時ディレクトリにダウンロード
        localfilename = os.path.join(tmpdir.name, filename)
        fp = open(localfilename, 'wb')
        fp.write(response['Body'].read())
        fp.close()

        # 暗号化する
        # パスワードは仮に「mypassword」とする
        zipfilename = tempfile.mkstemp(suffix='.zip')[1]
        os.chdir(tmpdir.name)
        pyminizip.compress(localfilename, None, zipfilename, 'mypassword', 0)

        # もうひとつのパケットに書き込む
        # 環境変数から書き出し先のバケット名を取
        destbucketname = os.environ['OutputBucket']

        # ファイルにアクセスするためのオブジェクトを取得
        obj2 = s3.Object(destbucketname, filename + '.zip')

        # アップロード
        response = obj2.put(
            Body = open(zipfilename, 'rb')
        )

        # 一時ファイルのクリーンアップ
        tmpdir.cleanup()
