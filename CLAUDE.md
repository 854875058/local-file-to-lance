# Claude AI 编码规则

本文件记录了在与 Claude AI 协作开发过程中需要遵守的规则和最佳实践。

## 核心规则

### 1. 方案先行原则
**在编写任何代码之前，请先描述你的方案并等待批准。如果需求不明确，在编写任何代码之前务必提出澄清问题。**

- 先理解需求，再动手编码
- 方案需要清晰描述实现思路、涉及的文件、主要步骤
- 等待用户确认后再开始实施

### 2. 任务分解原则
**如果一项任务需要修改超过3个文件，请先停下来，将其分解成更小的任务。**

- 大任务容易出错，小任务更可控
- 每个子任务应该聚焦单一目标
- 分步实施，逐步验证

### 3. 测试驱动原则
**编写代码后，列出可能出现的问题，并建议相应的测试用例来覆盖这些问题。**

- 主动思考边界情况和异常场景
- 提供具体的测试步骤或测试代码
- 确保代码的健壮性

### 4. Bug 修复原则
**当发现 bug 时，首先要编写一个能够重现该 bug 的测试，然后不断修复它，直到测试通过为止。**

- 先重现问题，再修复问题
- 测试用例作为修复的验收标准
- 避免盲目修改代码

### 5. 持续改进原则
**每次我纠正你之后，就在 CLAUDE.md 文件中添加一条新规则，这样就不会再发生这种情况了。**

- 从错误中学习
- 规则会不断完善
- 保持文档更新

### 6. 代码提交原则
**完成代码修改后，必须立即自动提交到 Git，不要等用户提醒。**

- 每次修改代码后立即执行 `git add -A` 和 `git commit`
- 提交信息应清晰描述修改内容和原因
- 提交后执行 `git push` 推送到远程仓库
- 提交完成后，明确说明改动了哪些文件及具体修改内容

### 7. 自验收原则
**每完成一个模块、接口或代码修改后，必须自行运行验证，确认功能正常后才算完成。验证不通过则持续修复，直到通过为止。**

- 写完代码不等于完成——必须跑通才算交付
- 验证方式视情况而定：能跑单元测试就跑测试，不能跑测试就用 `python -c` 或脚本做冒烟验证
- 对于语法和导入问题，至少执行 `python -c "import ast; ast.parse(open('文件路径').read())"` 确认无语法错误
- 对于接口/模块修改，构造最小调用验证核心逻辑是否正常返回
- 如果验证发现问题，立即修复并重新验证，循环直到通过
- 不要把未经验证的代码提交给用户

### 8. langchain 依赖注意事项
**本项目使用 `langchain-text-splitters` 包（而非 `langchain` 主包）来导入 `RecursiveCharacterTextSplitter`。**

- langchain 1.x 已将 `langchain.text_splitter` 模块移除，必须单独安装 `langchain-text-splitters`
- 正确的 import：`from langchain_text_splitters import RecursiveCharacterTextSplitter`
- 安装命令：`pip install langchain-text-splitters`
- `models_loader.py` 中的 fallback import（`from langchain.text_splitter import ...`）在 langchain 1.x 下无效，不要依赖它

### 9. 依赖完整性验证原则
**每次修改代码后，必须用 `python -c "import ..."` 验证所有涉及模块的依赖是否已安装，不能只检查语法。**

- 语法检查（`ast.parse`）不能发现缺失依赖，必须实际执行 import
- 本项目核心依赖：`sentence-transformers`、`langchain-text-splitters`、`nicegui`、`lancedb`、`pyarrow`、`boto3`、`paramiko`、`psutil`、`pandas`、`numpy`、`whisper`、`pypdf`、`python-docx`、`python-pptx`、`pdf2image`、`Pillow`
- 切换前端框架（如 Streamlit → NiceGUI）后，要验证新入口文件的全部 import 链路

---

*最后更新: 2026-02-14*
