from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor


OUT = r"E:\OneDrive\block\AXI2CHI_OrderBuffer_方案权衡.pptx"

BG = RGBColor(7, 15, 29)
PANEL = RGBColor(14, 27, 47)
PANEL_2 = RGBColor(18, 34, 56)
WHITE = RGBColor(241, 246, 252)
MUTED = RGBColor(158, 174, 197)
CYAN = RGBColor(46, 205, 224)
BLUE = RGBColor(76, 139, 245)
BLUE_D = RGBColor(27, 65, 120)
ORANGE = RGBColor(255, 166, 64)
ORANGE_D = RGBColor(112, 65, 23)
GREEN = RGBColor(78, 211, 151)
GREEN_D = RGBColor(19, 77, 58)
GRID = RGBColor(48, 67, 92)
RED = RGBColor(247, 112, 123)
FONT = "Microsoft YaHei"


def set_bg(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def add_text(slide, x, y, w, h, text, size=12, color=WHITE, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, margin=0.06):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_box(slide, x, y, w, h, text="", fill=PANEL_2, line=GRID,
            radius=True, size=12, color=WHITE, bold=False, align=PP_ALIGN.CENTER):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(1.0)
    if text:
        tf = shp.text_frame
        tf.clear()
        tf.margin_left = Inches(0.08)
        tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.03)
        tf.margin_bottom = Inches(0.03)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = text
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return shp


def add_arrow(slide, x1, y1, x2, y2, color=MUTED, width=1.6):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = color
    ln.line.width = Pt(width)
    ln.line.end_arrowhead = True
    return ln


def pill(slide, x, y, w, text, accent=CYAN):
    shp = add_box(slide, x, y, w, 0.34, text, fill=RGBColor(13, 31, 52), line=accent,
                  size=9.5, color=WHITE, bold=False)
    shp.line.transparency = 25
    return shp


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)

# Header
accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.38), Inches(0.30), Inches(0.06), Inches(0.65))
accent.fill.solid(); accent.fill.fore_color.rgb = CYAN; accent.line.fill.background()
add_text(slide, 0.55, 0.24, 8.8, 0.43, "AXI2CHI Order Buffer｜QoS调度与有序释放解耦",
         size=23, bold=True)
add_text(slide, 0.56, 0.67, 7.9, 0.28,
         "设计目标：同 AWID 严格保序，不同 AWID 按 1-bit QoS 分流",
         size=10.5, color=MUTED)

pill(slide, 9.08, 0.34, 1.05, "AWID 11-bit")
pill(slide, 10.22, 0.34, 0.92, "QoS 1-bit", ORANGE)
pill(slide, 11.23, 0.34, 1.62, "High / Low 双通道", GREEN)

# Main panels
add_box(slide, 0.38, 1.15, 7.42, 5.58, fill=PANEL, line=GRID, radius=True)
add_box(slide, 7.98, 1.15, 4.97, 5.58, fill=PANEL, line=GRID, radius=True)
add_text(slide, 0.66, 1.31, 4.4, 0.34, "推荐架构｜浅双 FIFO 调度 + 链表有序释放", 14, bold=True)
add_text(slide, 8.25, 1.31, 3.9, 0.34, "方案权衡｜仅比较 axi_buffer 实现", 14, bold=True)

# Architecture diagram
add_box(slide, 0.68, 2.42, 1.00, 0.70, "AXI\n事务", fill=RGBColor(24, 49, 77), line=BLUE,
        size=12, bold=True)
add_arrow(slide, 1.68, 2.77, 2.08, 2.77, CYAN)
add_box(slide, 2.08, 2.22, 1.40, 1.10, "AWID 检查\n通道绑定", fill=RGBColor(23, 55, 77), line=CYAN,
        size=12, bold=True)

add_text(slide, 1.98, 1.78, 1.75, 0.30, "新 AWID：按 QoS", 9.5, color=MUTED, align=PP_ALIGN.CENTER)
add_text(slide, 1.84, 3.40, 2.00, 0.30, "已存在：沿用绑定通道", 9.5, color=MUTED, align=PP_ALIGN.CENTER)

add_arrow(slide, 3.48, 2.52, 3.93, 2.05, ORANGE)
add_arrow(slide, 3.48, 3.03, 3.93, 3.50, BLUE)
add_box(slide, 3.93, 1.70, 1.62, 0.72, "HIGH FIFO\nDepth = 2", fill=ORANGE_D, line=ORANGE,
        size=11.5, bold=True)
add_box(slide, 3.93, 3.22, 1.62, 0.72, "LOW FIFO\nDepth = 2", fill=BLUE_D, line=BLUE,
        size=11.5, bold=True)

add_arrow(slide, 5.55, 2.06, 5.98, 2.54, ORANGE)
add_arrow(slide, 5.55, 3.58, 5.98, 3.10, BLUE)
add_box(slide, 5.98, 2.36, 1.18, 0.92, "2:1\n仲裁", fill=RGBColor(35, 49, 75), line=GREEN,
        size=12, bold=True)
add_arrow(slide, 7.16, 2.82, 7.54, 2.82, GREEN)
add_text(slide, 6.97, 2.32, 0.63, 0.28, "TXREQ", 8.5, color=GREEN, bold=True, align=PP_ALIGN.CENTER)

# Lower flow / response ordering
add_box(slide, 1.20, 4.55, 4.64, 1.15, fill=RGBColor(16, 43, 48), line=GREEN, radius=True)
add_text(slide, 1.45, 4.68, 4.10, 0.30, "Linked List / Outstanding Table", 13, bold=True, align=PP_ALIGN.CENTER)
add_text(slide, 1.45, 5.02, 4.10, 0.25, "AWID · next_ptr · is_head · done", 10, color=MUTED, align=PP_ALIGN.CENTER)
add_text(slide, 1.45, 5.30, 4.10, 0.23, "RXRSP 可乱序，BRESP 同 AWID 有序释放", 9.5, color=GREEN, align=PP_ALIGN.CENTER)

add_box(slide, 6.16, 4.62, 1.10, 0.46, "TXDAT", fill=RGBColor(43, 54, 72), line=MUTED,
        size=10.5, bold=True)
add_box(slide, 6.16, 5.21, 1.10, 0.46, "BRESP", fill=RGBColor(43, 54, 72), line=MUTED,
        size=10.5, bold=True)
add_arrow(slide, 5.84, 5.00, 6.16, 4.85, GREEN, 1.4)
add_arrow(slide, 5.84, 5.25, 6.16, 5.44, GREEN, 1.4)

# Clarify separation
add_text(slide, 0.80, 6.05, 6.30, 0.30,
         "调度顺序由 axi_buffer 保证｜完成与释放顺序由 linkedlist 保证",
         10.2, color=CYAN, bold=True, align=PP_ALIGN.CENTER)

# Tradeoff table
x0, y0 = 8.25, 1.82
col = [1.12, 1.55, 1.70]
headers = ["维度", "双 FIFO（选用）", "按 AWID 建链"]
fills = [RGBColor(28, 43, 66), RGBColor(28, 64, 65), RGBColor(48, 43, 61)]
for i, (hdr, cw) in enumerate(zip(headers, col)):
    xx = x0 + sum(col[:i])
    add_box(slide, xx, y0, cw, 0.48, hdr, fill=fills[i], line=GRID, radius=False,
            size=10.2, bold=True)

rows = [
    ("QoS方式", "High / Low\n二选一", "所有链头\n按 QoS 仲裁"),
    ("High QoS\n响应性", "同 AWID 暂时\n继承通道", "成为链头后\n立即重新提权"),
    ("Depth=2", "位置等待\n最多 1 项*", "额外收益\n相对有限"),
    ("控制逻辑", "简单", "head/tail/next\n多链管理"),
    ("动态功耗", "预期较低", "预期较高"),
    ("调度灵活性", "中", "高"),
]
rh = 0.56
for r, row in enumerate(rows):
    yy = y0 + 0.48 + r * rh
    for c, (txt, cw) in enumerate(zip(row, col)):
        xx = x0 + sum(col[:c])
        fill = RGBColor(16, 31, 51) if r % 2 == 0 else RGBColor(20, 36, 57)
        color = MUTED if c == 0 else WHITE
        if c == 1 and r in (2, 3, 4):
            color = GREEN
        add_box(slide, xx, yy, cw, rh, txt, fill=fill, line=GRID, radius=False,
                size=9.3, color=color, bold=(c == 0), align=PP_ALIGN.CENTER)

add_text(slide, 8.27, 5.82, 4.30, 0.30,
         "* 指 FIFO 中的位置等待；实际周期仍受仲裁、credit 与背压影响",
         8.2, color=MUTED)

# Decision banner
add_box(slide, 8.24, 6.14, 4.43, 0.42,
        "决策：Depth=2 双 FIFO + 后级 Linked List",
        fill=GREEN_D, line=GREEN, size=11.5, color=WHITE, bold=True)

# Tiny footer
add_text(slide, 0.44, 7.10, 12.45, 0.18,
         "Accepted trade-off：同 AWID 未清空期间，后续事务沿用已有通道；以更低控制复杂度与预期功耗换取有限的 QoS 灵活性。",
         8.5, color=MUTED, align=PP_ALIGN.CENTER)

# Metadata
prs.core_properties.title = "AXI2CHI Order Buffer QoS调度与有序释放解耦"
prs.core_properties.subject = "双FIFO与按AWID链表调度方案权衡"
prs.core_properties.author = "Codex"
prs.save(OUT)
print(OUT)
