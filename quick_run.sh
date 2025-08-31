#!/bin/bash
# AI对冲基金快速运行脚本 (Mac/Linux)
# 使用预设配置自动运行，无需每次手动配置

echo "🎯 AI对冲基金快速运行器"
echo "================================"

# 检查配置文件是否存在
if [ ! -f "config.yaml" ]; then
    echo "⚠️  配置文件不存在，正在创建默认配置..."
    poetry run python run_with_config.py --create-config
    echo
    echo "📝 请编辑 config.yaml 文件设置你的参数："
    echo "   - 股票代码 (tickers)"
    echo "   - 时间范围 (start_date, end_date)"
    echo "   - AI分析师选择 (analysts)"
    echo "   - 模型配置 (model)"
    echo
    echo "编辑完成后再次运行此脚本"
    exit 1
fi

echo "✅ 找到配置文件: config.yaml"
echo

# 验证配置文件
echo "🔍 验证配置文件..."
poetry run python run_with_config.py --validate
if [ $? -ne 0 ]; then
    echo
    echo "❌ 配置文件验证失败，请检查配置"
    exit 1
fi

echo "✅ 配置文件验证通过"
echo

# 运行AI对冲基金
echo "🚀 开始运行AI对冲基金..."
echo
poetry run python run_with_config.py

echo
echo "🎉 运行完成！"
echo "📁 结果文件保存在 results/ 目录中"