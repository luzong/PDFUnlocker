# -*- coding: utf-8 -*-
# PDF解密工具 - 解除PDF文件的打印/复制/编辑权限限制
# 使用PyMuPDF库(fitz)进行PDF操作，Tkinter实现图形界面

# 导入操作系统相关模块，用于文件路径处理
import os
# 导入PyMuPDF库，别名fitz，用于PDF文件的读取和解密操作
import fitz  # PyMuPDF
# 从tkinter库导入所需组件：主窗口、标签、框架、字符串变量、按钮、文件对话框、消息框
from tkinter import Tk, Label, Frame, StringVar, Button, filedialog, messagebox
# 从tkinterdnd2库导入拖拽相关组件，实现文件拖拽功能
from tkinterdnd2 import DND_FILES, TkinterDnD
# 从PIL库导入Image和ImageTk，用于图片处理和显示
from PIL import Image, ImageTk
# 从tkinter.ttk导入进度条组件
from tkinter.ttk import Progressbar

# 定义PDF解密工具类，继承自object（Python3默认）
class PDFDecryptTool:
    # 类的构造函数，初始化GUI界面
    def __init__(self, root):
        # 将主窗口对象保存为实例属性
        self.root = root
        # 设置窗口标题
        self.root.title("PDF解密工具 - 解除打印/复制/编辑权限")
        # 设置窗口固定大小为500x420像素（宽x高）
        self.root.geometry("500x385")
        # 设置窗口大小不可调整（宽、高都固定）
        self.root.resizable(False, False)

        # 定义窗口图标路径（根目录下的256x256锁图标）
        icon_path = "img_256.png"
        # 检查图标文件是否存在
        if os.path.exists(icon_path):
            try:
                # 使用PIL打开图标文件
                icon_img = Image.open(icon_path)
                # 将PIL图片转换为Tkinter可用的PhotoImage对象
                photo_icon = ImageTk.PhotoImage(icon_img)
                # 设置窗口图标，False表示不应用于所有顶层窗口
                self.root.iconphoto(False, photo_icon)
            except Exception as e:
                # 捕获并打印图标加载异常信息
                print(f"窗口图标加载失败: {e}")

        # 定义实例变量：导出目录路径（StringVar用于Tkinter动态绑定）
        self.export_path = StringVar()
        # 定义实例变量：进度条文字（StringVar用于Tkinter动态绑定）
        self.progress_text = StringVar()
        # 设置初始进度文字
        self.progress_text.set("等待拖拽上传文件")
        # 获取用户桌面路径作为默认导出目录
        desktop = os.path.expanduser("~/Desktop")
        # 设置默认导出目录到桌面
        self.export_path.set(desktop)

        # ========== 拖拽背景区域 固定500*300 ==========
        # 创建一个固定大小的框架作为拖拽区域容器
        drop_frame = Frame(root, width=500, height=300, bd=0)
        # 将框架放置到窗口，上下外边距0，左右外边距0
        drop_frame.pack(pady=0, padx=0)
        # 锁定框架尺寸为500x300，防止内部组件拉伸框架
        drop_frame.pack_propagate(False)  # 锁定frame尺寸500x300

        # 定义背景图片路径
        bg_img_path = "img.png"
        # 初始化背景图片对象为None
        self.bg_photo = None
        # 检查背景图片文件是否存在
        if os.path.exists(bg_img_path):
            try:
                # 使用PIL打开背景图片文件
                bg_image = Image.open(bg_img_path)
                # 将背景图片缩放为500x300，使用LANCZOS算法保持画质
                bg_image = bg_image.resize((500, 300), Image.Resampling.LANCZOS)
                # 将PIL图片转换为Tkinter可用的PhotoImage对象
                self.bg_photo = ImageTk.PhotoImage(bg_image)
            except Exception as e:
                # 捕获并打印背景图加载异常信息
                print(f"拖拽背景图加载失败: {e}")

        # 创建标签组件，显示背景图片，背景色白色，鼠标悬停显示手型光标
        self.drop_label = Label(drop_frame, image=self.bg_photo, bg="#ffffff", cursor="hand2")
        # 将标签铺满整个拖拽框架区域
        self.drop_label.pack(expand=True, fill="both")

        # 为拖拽框架注册文件拖拽目标类型（DND_FILES表示接受文件）
        drop_frame.drop_target_register(DND_FILES)
        # 绑定拖拽事件，当文件拖放到框架时触发on_file_drop方法
        drop_frame.dnd_bind("<<Drop>>", self.on_file_drop)
        # 为拖拽标签也注册文件拖拽目标类型
        self.drop_label.drop_target_register(DND_FILES)
        # 绑定拖拽事件到标签，确保整个区域都能响应拖拽
        self.drop_label.dnd_bind("<<Drop>>", self.on_file_drop)
        # 绑定鼠标左键点击事件，点击背景图时触发文件选择对话框
        self.drop_label.bind("<Button-1>", self.click_open_file_dialog)

        # ========== 第一底部行：导出目录选择 ==========
        # 创建导出目录选择区域的框架
        path_frame = Frame(root, width=500)
        # 将框架放置到窗口，上下外边距10，左右外边距10，水平填充
        path_frame.pack(pady=10, padx=10, fill="x")
        # 创建"导出目录："标签，使用微软雅黑字体，字号10
        Label(path_frame, text="导出目录：", font=("微软雅黑", 10)).pack(side="left")
        # 创建显示导出路径的标签，动态绑定self.export_path变量
        Label(path_frame, textvariable=self.export_path, font=("微软雅黑", 9), fg="#333").pack(side="left", padx=5, fill="x", expand=True)
        # 创建"选择目录"按钮，点击时调用select_export_dir方法
        Button(path_frame, text="选择目录", command=self.select_export_dir, font=("微软雅黑", 9)).pack(side="right")

        # ========== 第二底部行：进度条 + 进度文字 ==========
        # 创建进度条区域的框架
        progress_frame = Frame(root, width=500)
        # 将框架放置到窗口，上下外边距0，左右外边距10，水平填充
        progress_frame.pack(pady=0, padx=10, fill="x")
        # 创建进度条组件，模式为确定模式（显示具体进度）
        self.progress_bar = Progressbar(progress_frame, length=360, mode="determinate")
        # 将进度条放置到框架左侧
        self.progress_bar.pack(side="left")
        # 创建显示进度文字的标签，动态绑定self.progress_text变量
        Label(progress_frame, textvariable=self.progress_text, font=("微软雅黑", 9), fg="#222").pack(side="right", padx=8)

    # 鼠标点击背景图触发的方法，打开文件选择对话框
    def click_open_file_dialog(self, event):
        """点击背景图片，弹出PDF文件选择窗口"""
        # 弹出文件选择对话框，允许选择多个PDF文件
        file_paths = filedialog.askopenfilenames(
            title="选择需要解密的PDF文件",  # 对话框标题
            filetypes=[("PDF文档", "*.pdf"), ("所有文件", "*.*")]  # 文件类型过滤器
        )
        # 如果用户未选择任何文件，直接返回
        if not file_paths:
            return
        # 调用统一的PDF处理方法处理选中的文件
        self.process_pdf_list(file_paths)

    # 选择导出目录的方法
    def select_export_dir(self):
        # 弹出目录选择对话框
        folder = filedialog.askdirectory(title="选择解密后PDF保存目录")
        # 如果用户选择了目录，更新导出路径变量
        if folder:
            self.export_path.set(folder)

    # 文件拖拽到窗口触发的方法
    def on_file_drop(self, event):
        """拖拽文件触发处理"""
        # 解析拖拽事件中的文件路径列表
        file_paths = self.root.tk.splitlist(event.data)
        # 过滤出以.pdf结尾的文件（不区分大小写）
        pdf_files = [f for f in file_paths if f.lower().endswith(".pdf")]
        # 如果没有找到PDF文件
        if not pdf_files:
            # 弹出警告提示框
            messagebox.showwarning("提示", "拖拽的文件不是PDF格式！")
            # 更新进度文字提示
            self.progress_text.set("未识别到PDF文件")
            # 重置进度条为0
            self.progress_bar["value"] = 0
            # 直接返回，不进行后续处理
            return
        # 调用统一的PDF处理方法处理拖拽的PDF文件
        self.process_pdf_list(pdf_files)

    # 统一处理PDF文件列表的核心方法
    def process_pdf_list(self, pdf_files):
        """统一处理PDF列表（拖拽/点击上传共用）"""
        # 获取PDF文件总数
        total = len(pdf_files)
        # 初始化成功计数器为0
        success_count = 0
        # 初始化失败列表，用于记录处理失败的文件
        fail_list = []
        # 获取当前设置的导出目录路径
        out_dir = self.export_path.get()

        # 重置进度条
        # 设置进度条当前值为0
        self.progress_bar["value"] = 0
        # 更新进度文字为初始状态
        self.progress_text.set(f"0/{total} 处理中")
        # 强制刷新GUI界面，显示更新后的进度
        self.root.update()

        # 遍历PDF文件列表，enumerate返回索引和文件路径
        for idx, pdf_file in enumerate(pdf_files):
            try:
                # 使用PyMuPDF打开PDF文件
                doc = fitz.open(pdf_file)
                # 检查PDF是否加密且无法用空密码打开
                if doc.is_encrypted and doc.authenticate("") is False:
                    # 将失败信息添加到失败列表
                    fail_list.append(f"{os.path.basename(pdf_file)}：存在打开密码，无法解密")
                    # 关闭PDF文档对象
                    doc.close()
                    # 跳过当前文件，继续处理下一个
                    continue
                # 解密保存：生成新文件名，前缀为"解密_"
                save_name = f"解密_{os.path.basename(pdf_file)}"
                # 拼接完整的保存路径
                save_full = os.path.join(out_dir, save_name)
                # 保存解密后的PDF文件，garbage=4表示彻底清理，clean=True表示清理冗余数据
                doc.save(save_full, garbage=4, clean=True)
                # 关闭PDF文档对象
                doc.close()
                # 成功计数器加1
                success_count += 1
            except Exception as e:
                # 捕获处理过程中的异常，记录失败信息
                fail_list.append(f"{os.path.basename(pdf_file)}：{str(e)}")

            # 更新进度条与文字
            # 当前处理序号（从1开始）
            current = idx + 1
            # 计算当前进度百分比
            percent = int((current / total) * 100)
            # 更新进度条值
            self.progress_bar["value"] = percent
            # 更新进度文字
            self.progress_text.set(f"{current}/{total} 已处理")
            # 强制刷新GUI界面，实时显示进度
            self.root.update()

        # 处理完成弹窗
        # 构建结果消息，包含成功数量和保存目录
        msg = f"解密完成！成功：{success_count} 个文件\n保存目录：{out_dir}"
        # 如果有失败文件，追加失败列表到消息中
        if fail_list:
            msg += "\n\n失败列表：\n" + "\n".join(fail_list)
        # 弹出消息框显示处理结果
        messagebox.showinfo("执行结果", msg)
        # 更新进度文字为最终状态
        self.progress_text.set(f"全部完成，成功{success_count}个")

# 程序入口：当脚本直接运行时执行
if __name__ == "__main__":
    # 创建支持拖拽功能的Tkinter主窗口
    window = TkinterDnD.Tk()
    # 创建PDF解密工具实例
    app = PDFDecryptTool(window)
    # 启动Tkinter事件循环，保持窗口显示
    window.mainloop()