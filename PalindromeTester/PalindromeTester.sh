#!/bin/bash
# PalindromeTester
# Author: Xu Zhen 徐震 3180105504
# 我们注释掉了一些测试用的信息打印语句，读者可取消注释以观察程序运行过程
# 我们通过反转并对比字符串来检测其是否为回文
# 若我们并非在写脚本，我们或许会通过头尾两个指针做对比来实现这一功能
# 但在脚本语言中实现相关的操作会显得很麻烦
read -p "The string you want to test is: " word
trimmed=""
reversed=""
# 我们通过下标遍历字符串，剔除非字母部分
for i in $(seq 0 $(expr ${#word} - 1))
do
	thechar=${word:i:1}
	# echo "The letter at position $i is: $thechar"
	if [[ "$thechar" =~ [a-zA-Z] ]]
	then
		# echo "And I'm adding it to the trimmed string"
		trimmed+=$thechar
		# 我们可以在此处通过本语句构建反转了的字符串
		# 这样就不需要在下面调用reversed=$(echo $trimmed | rev)
		reversed="$thechar$reversed"
	fi
done
echo "The trimmed string would be: $trimmed"
echo -n "The reversed version of the trimmed: "
# 除了在循环中直接反转字符串，我们也可以通过管道调用rev命令获取其反转以检测回文
# reversed=$(echo $trimmed | rev)
echo $reversed
if [ $reversed = $trimmed ]
then
	echo "Gotcha! You're a palindrome!"
else
	echo "Well, you're not a palindrome!"
fi
