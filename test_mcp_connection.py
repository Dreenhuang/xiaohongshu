#!/usr/bin/env python3
"""
测试小红书MCP连接的简化脚本
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(r'J:\AIAI\autoxiaohongshu\Redbook-Search-Comment-MCP2.0')

async def test_direct_functions():
    """直接测试MCP函数"""
    print("🔧 开始测试MCP函数...")
    
    try:
        # 导入MCP函数
        from xiaohongshu_mcp import login, search_notes, post_comment
        
        print("✅ MCP函数导入成功")
        
        # 测试登录
        print("🔐 尝试登录小红书...")
        login_result = await login()
        print(f"登录结果: {login_result}")
        
        if "成功" in str(login_result) or "已登录" in str(login_result):
            print("✅ 登录成功！浏览器会话已建立")
            
            # 测试搜索功能
            print("🔍 测试搜索功能...")
            search_result = await search_notes("全屋定制", limit=3)
            print(f"搜索结果: {search_result}")
            
            if "搜索结果" in str(search_result):
                print("✅ 搜索功能正常")
                
                # 解析搜索结果获取第一个URL
                lines = search_result.split('\n')
                first_url = None
                for line in lines:
                    if "链接:" in line:
                        first_url = line.replace("链接:", "").strip()
                        break
                
                if first_url:
                    print(f"🎯 尝试为第一个笔记发布测试评论...")
                    print(f"笔记URL: {first_url}")
                    
                    comment_result = await post_comment(
                        first_url, 
                        "测试评论 - 我自荐，可以看看我的主页"
                    )
                    print(f"评论结果: {comment_result}")
                    
                    if "成功" in str(comment_result):
                        print("✅ 评论发布成功！浏览器会话稳定")
                        return True
                    else:
                        print("❌ 评论发布失败，可能遇到反爬虫机制")
                        print("具体错误:", comment_result)
                        return False
                else:
                    print("❌ 无法从搜索结果中提取URL")
                    return False
            else:
                print("❌ 搜索功能异常")
                print("搜索结果:", search_result)
                return False
        else:
            print("❌ 登录失败，无法建立浏览器会话")
            print("登录结果:", login_result)
            return False
            
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def diagnose_browser_session():
    """诊断浏览器会话问题"""
    print("\n🔍 诊断浏览器会话问题...")
    
    try:
        from xiaohongshu_mcp import ensure_browser, main_page, browser_context
        
        # 检查浏览器状态
        browser_status = await ensure_browser()
        print(f"浏览器状态: {browser_status}")
        
        if main_page:
            print("✅ 主页面存在")
            try:
                current_url = main_page.url
                print(f"当前页面URL: {current_url}")
            except Exception as e:
                print(f"❌ 无法获取当前页面URL: {e}")
        else:
            print("❌ 主页面不存在")
            
        if browser_context:
            print("✅ 浏览器上下文存在")
            try:
                pages = browser_context.pages
                print(f"浏览器页面数量: {len(pages)}")
            except Exception as e:
                print(f"❌ 无法获取浏览器页面: {e}")
        else:
            print("❌ 浏览器上下文不存在")
            
    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🌸 小红书MCP连接测试工具")
    print("=" * 60)
    
    # 运行测试
    success = asyncio.run(test_direct_functions())
    
    if not success:
        # 如果测试失败，进行诊断
        asyncio.run(diagnose_browser_session())
    
    print("=" * 60)
    print("测试完成")
    
    if success:
        print("🎉 所有测试通过！浏览器会话稳定")
    else:
        print("⚠️ 测试失败，浏览器会话可能不稳定")
        print("\n💡 解决建议:")
        print("1. 重启MCP服务")
        print("2. 检查网络连接")
        print("3. 手动登录小红书网站")
        print("4. 降低操作频率")
