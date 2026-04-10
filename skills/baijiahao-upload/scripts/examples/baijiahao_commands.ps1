# PowerShell examples for the installed sau CLI.

# account_name is user-defined. One account_name maps to one account file.
# You can prepare multiple account names and run them in parallel.
$account = "account_a"
$articleImages = @("images/1.png", "images/2.png")

sau baijiahao login --account $account --headed
sau baijiahao check --account $account

sau baijiahao upload-article `
  --account $account `
  --title "百家号图文文章标题" `
  --content "这里是文章正文内容，支持多段文字。" `
  --images $articleImages `
  --tags "标签1,标签2" `
  --headed
