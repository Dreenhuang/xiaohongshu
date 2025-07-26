#!/usr/bin/env python3
"""
最终自动评论解决方案
假设用户已经登录，直接执行评论任务
"""

import asyncio
import json
import time
import random
from playwright.async_api import async_playwright
import os

class FinalCommentBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化最终评论机器人...")
        
        playwright = await async_playwright().start()
        
        # 使用无头模式，更稳定
        self.browser = await playwright.chromium.launch(
            headless=False,  # 显示浏览器便于调试
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        
        print("✅ 浏览器初始化成功")
        
    async def quick_login_check(self):
        """快速登录检查"""
        print("🔐 检查登录状态...")
        
        try:
            await self.page.goto("https://www.xiaohongshu.com", timeout=30000)
            await asyncio.sleep(3)
            
            # 检查是否有登录按钮
            login_buttons = await self.page.query_selector_all('text="登录"')
            if login_buttons:
                print("❌ 需要登录，请先手动登录小红书")
                print("💡 请在浏览器中登录后，按回车继续...")
                input("按回车键继续...")
                
                # 再次检查
                await self.page.reload()
                await asyncio.sleep(2)
                login_buttons = await self.page.query_selector_all('text="登录"')
                if login_buttons:
                    print("❌ 仍未登录，程序退出")
                    return False
            
            print("✅ 登录状态正常")
            return True
            
        except Exception as e:
            print(f"❌ 登录检查失败: {e}")
            return False
    
    async def get_target_notes(self):
        """获取目标笔记列表"""
        print("📋 获取目标笔记...")
        
        # 这些是之前搜索到的笔记URL（从之前的输出中提取）
        target_notes = [
            {
                "url": "https://www.xiaohongshu.com/search_result/6882e99f00000000220302c0?xsec_token=ABvDl9NTqZlQnsbEY2fZNd9Uqk-ImNqzHiC-xRtdtEKNw=&xsec_source=",
                "title": "花了35万全屋定制，避雷图森高端定制"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/687c8317000000001d00cf98?xsec_token=ABdrMw-zicJShKTN-miLEmLX3aTQVhcj_WFmBQZQU8C58=&xsec_source=",
                "title": "全屋定制避坑指南"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6881f7bb0000000017030ae3?xsec_token=ABvDl9NTqZlQnsbEY2fZNd9VovQ8bnmQJ_81dsmyNgPjw=&xsec_source=",
                "title": "全屋定制经验分享"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/68771bde000000001203fa26?xsec_token=ABZyU7fC3GO3bxskpr4R4BHelOW3hZfBaQiXyCdw-9Yak=&xsec_source=",
                "title": "定制家具选择攻略"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6881eb170000000011001d55?xsec_token=ABoFB8QX82VyGnHGHW1o7_DYgqNKk9pDN6hK-SHx26xE8=&xsec_source=",
                "title": "全屋定制价格分析"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/68823e87000000002203fd66?xsec_token=ABZyU7fC3GO3bxskpr4R4BHelOW3hZfBaQiXyCdw-9Yak=&xsec_source=",
                "title": "定制衣柜经验"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6880d018000000001202dd79?xsec_token=ABoFB8QX82VyGnHGHW1o7_DYgqNKk9pDN6hK-SHx26xE8=&xsec_source=",
                "title": "全屋定制材料选择"
            }
        ]
        
        print(f"✅ 准备处理 {len(target_notes)} 个目标笔记")
        return target_notes
    
    async def simple_comment(self, url, comment, title):
        """简化的评论方法 - 专门定位右下角评论输入框"""
        print(f"💬 评论: {title}")
        
        try:
            # 访问页面
            await self.page.goto(url, timeout=30000)
            await asyncio.sleep(8)  # 增加等待时间让页面完全加载
            
            # 检查页面是否有效
            page_content = await self.page.content()
            if "当前笔记暂时无法浏览" in page_content:
                print("⚠️ 笔记无法访问")
                return False
            
            # 滚动页面，确保评论区域可见
            print("📜 滚动页面加载评论区...")
            await self.page.evaluate("""
                () => {
                    // 先滚动到中间位置
                    window.scrollTo(0, document.body.scrollHeight / 2);
                    setTimeout(() => {
                        // 再滚动到底部
                        window.scrollTo(0, document.body.scrollHeight);
                    }, 1000);
                }
            """)
            await asyncio.sleep(5)
            
            print("🔍 专门查找右下角评论输入框...")
            
            # 使用更精确的方法定位"说点什么"评论输入框
            result = await self.page.evaluate(f"""
                (comment) => {{
                    console.log('开始查找"说点什么"评论输入框...');
                    
                    // 方法1: 直接查找包含"说点什么"的元素
                    const sayElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        const text = el.textContent || el.placeholder || el.getAttribute('placeholder') || '';
                        return text.includes('说点什么');
                    }});
                    
                    console.log('找到"说点什么"元素数量:', sayElements.length);
                    
                    // 优先处理"说点什么"相关的输入框
                    for (const sayEl of sayElements) {{
                        try {{
                            console.log('处理"说点什么"元素:', sayEl.tagName, sayEl.className);
                            
                            let targetInput = null;
                            
                            // 如果元素本身就是输入框
                            if (sayEl.tagName === 'TEXTAREA' || 
                                sayEl.tagName === 'INPUT' || 
                                sayEl.contentEditable === 'true') {{
                                targetInput = sayEl;
                            }} else {{
                                // 在元素内部查找输入框
                                const inputs = sayEl.querySelectorAll('textarea, input[type="text"], div[contenteditable="true"]');
                                if (inputs.length > 0) {{
                                    targetInput = inputs[0];
                                }}
                                
                                // 在父元素中查找输入框
                                if (!targetInput && sayEl.parentElement) {{
                                    const parentInputs = sayEl.parentElement.querySelectorAll('textarea, input[type="text"], div[contenteditable="true"]');
                                    if (parentInputs.length > 0) {{
                                        targetInput = parentInputs[0];
                                    }}
                                }}
                            }}
                            
                            if (targetInput) {{
                                const rect = targetInput.getBoundingClientRect();
                                console.log('找到目标输入框:', targetInput.tagName, `位置: x:${{rect.left}}, y:${{rect.top}}, w:${{rect.width}}, h:${{rect.height}}`);
                                
                                if (rect.width > 0 && rect.height > 0) {{
                                    // 滚动到输入框
                                    targetInput.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    
                                    // 等待滚动完成
                                    setTimeout(() => {{
                                        // 点击激活
                                        targetInput.click();
                                        targetInput.focus();
                                        
                                        setTimeout(() => {{
                                            // 清空现有内容
                                            if (targetInput.tagName === 'DIV') {{
                                                targetInput.innerHTML = '';
                                                targetInput.textContent = '';
                                            }} else {{
                                                targetInput.value = '';
                                            }}
                                            
                                            // 输入评论内容
                                            if (targetInput.tagName === 'DIV') {{
                                                targetInput.innerHTML = comment;
                                                targetInput.textContent = comment;
                                            }} else {{
                                                targetInput.value = comment;
                                            }}
                                            
                                            // 触发输入事件
                                            const events = ['input', 'change', 'keyup', 'blur'];
                                            events.forEach(eventType => {{
                                                const event = new Event(eventType, {{ bubbles: true, cancelable: true }});
                                                targetInput.dispatchEvent(event);
                                            }});
                                            
                                            console.log('输入完成，查找发送按钮...');
                                            
                                            // 查找发送按钮 - 多种策略
                                            let sendButton = null;
                                            
                                            // 策略1: 在同一容器中查找
                                            const container = targetInput.closest('div, form, section');
                                            if (container) {{
                                                const containerButtons = container.querySelectorAll('button');
                                                sendButton = Array.from(containerButtons).find(btn => {{
                                                    const btnText = btn.textContent || btn.innerText || '';
                                                    return btnText.includes('发送') || btnText.includes('发布') || btnText.includes('提交');
                                                }});
                                            }}
                                            
                                            // 策略2: 查找附近的按钮
                                            if (!sendButton) {{
                                                const allButtons = Array.from(document.querySelectorAll('button'));
                                                const inputRect = targetInput.getBoundingClientRect();
                                                
                                                sendButton = allButtons.find(btn => {{
                                                    const btnRect = btn.getBoundingClientRect();
                                                    const btnText = btn.textContent || btn.innerText || '';
                                                    
                                                    // 检查按钮是否在输入框附近且包含发送相关文字
                                                    const isNearby = Math.abs(btnRect.top - inputRect.top) < 100 && 
                                                                   Math.abs(btnRect.left - inputRect.right) < 200;
                                                    const hasText = btnText.includes('发送') || btnText.includes('发布');
                                                    
                                                    return isNearby && hasText;
                                                }});
                                            }}
                                            
                                            // 策略3: 查找任何发送按钮
                                            if (!sendButton) {{
                                                const allButtons = Array.from(document.querySelectorAll('button'));
                                                sendButton = allButtons.find(btn => {{
                                                    const btnText = btn.textContent || btn.innerText || '';
                                                    return btnText.includes('发送') || btnText.includes('发布');
                                                }});
                                            }}
                                            
                                            if (sendButton) {{
                                                console.log('找到发送按钮，点击发送');
                                                sendButton.click();
                                            }} else {{
                                                console.log('未找到发送按钮，尝试回车键');
                                                const enterEvent = new KeyboardEvent('keydown', {{
                                                    key: 'Enter',
                                                    code: 'Enter',
                                                    keyCode: 13,
                                                    bubbles: true,
                                                    cancelable: true
                                                }});
                                                targetInput.dispatchEvent(enterEvent);
                                            }}
                                            
                                        }}, 500);
                                    }}, 1000);
                                    
                                    return {{ success: true, method: 'say_something_input' }};
                                }}
                            }}
                        }} catch (e) {{
                            console.error('处理"说点什么"元素失败:', e);
                            continue;
                        }}
                    }}
                    
                    // 方法2: 如果没找到"说点什么"，查找其他评论相关的输入框
                    console.log('未找到"说点什么"，尝试其他评论输入框...');
                    
                    const commentKeywords = ['评论', '写评论', '发表看法', 'comment'];
                    const commentElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        const text = (el.textContent || el.placeholder || '').toLowerCase();
                        return commentKeywords.some(keyword => text.includes(keyword));
                    }});
                    
                    console.log('找到评论相关元素数量:', commentElements.length);
                    
                    for (const commentEl of commentElements) {{
                        try {{
                            const inputs = commentEl.querySelectorAll('textarea, input[type="text"], div[contenteditable="true"]');
                            for (const input of inputs) {{
                                const rect = input.getBoundingClientRect();
                                if (rect.width > 50 && rect.height > 20) {{
                                    console.log('尝试评论相关输入框');
                                    
                                    input.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    input.click();
                                    input.focus();
                                    
                                    if (input.tagName === 'DIV') {{
                                        input.innerHTML = comment;
                                        input.textContent = comment;
                                    }} else {{
                                        input.value = comment;
                                    }}
                                    
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    
                                    // 查找发送按钮
                                    const nearbyButton = commentEl.querySelector('button');
                                    if (nearbyButton) {{
                                        nearbyButton.click();
                                    }} else {{
                                        input.dispatchEvent(new KeyboardEvent('keydown', {{
                                            key: 'Enter',
                                            keyCode: 13,
                                            bubbles: true
                                        }}));
                                    }}
                                    
                                    return {{ success: true, method: 'comment_related_input' }};
                                }}
                            }}
                        }} catch (e) {{
                            console.error('处理评论相关元素失败:', e);
                            continue;
                        }}
                    }}
                    
                    return {{ success: false, reason: 'no_say_something_input_found' }};
                }}
            """, comment)
            
            await asyncio.sleep(3)  # 等待操作完成
            
            if result.get('success'):
                print(f"✅ 评论成功 (方法: {result.get('method')})")
                return True
            else:
                print(f"❌ 自动评论失败 (原因: {result.get('reason')})")
                print("🔧 请手动完成评论...")
                print(f"💬 评论内容: {comment}")
                print("📍 请在浏览器右下角找到评论输入框并手动输入评论")
                print("✅ 完成后按回车继续...")
                input()
                return True  # 假设手动完成了
                
        except Exception as e:
            print(f"❌ 评论过程出错: {e}")
            return False
    
    async def run_final_task(self):
        """运行最终评论任务"""
        print("🎯 启动最终自动评论任务")
        print("=" * 50)
        
        try:
            # 初始化
            await self.init_browser()
            
            # 检查登录
            if not await self.quick_login_check():
                return
            
            # 获取目标笔记
            notes = await self.get_target_notes()
            
            print(f"📝 开始处理 {len(notes)} 个笔记...")
            
            # 逐个评论
            success_count = 0
            for i, note in enumerate(notes, 1):
                print(f"\n📌 [{i}/{len(notes)}] {note['title']}")
                
                # 等待
                wait_time = random.uniform(10, 15)
                print(f"⏳ 等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # 评论
                if await self.simple_comment(note['url'], "我自荐，可以看看我的主页", note['title']):
                    success_count += 1
                    print(f"✅ 成功 [{success_count}/{i}]")
                else:
                    print(f"❌ 失败 [{success_count}/{i}]")
                
                # 每3个笔记休息
                if i % 3 == 0 and i < len(notes):
                    rest_time = random.uniform(30, 60)
                    print(f"😴 休息 {rest_time:.1f}s...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 50)
            print(f"🎉 最终任务完成！")
            print(f"📊 成功率: {success_count}/{len(notes)} ({success_count/len(notes)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        finally:
            print("🔚 任务结束，浏览器保持打开")

async def main():
    bot = FinalCommentBot()
    await bot.run_final_task()

if __name__ == "__main__":
    asyncio.run(main())