from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.dml.color import RGBColor


OUT = r"E:\OneDrive\block\AXI2CHI_OrderBuffer_Design_Review.pptx"

BG = RGBColor(7, 14, 27)
PANEL = RGBColor(14, 26, 44)
PANEL_ALT = RGBColor(18, 33, 54)
GRID = RGBColor(49, 68, 93)
WHITE = RGBColor(241, 246, 252)
MUTED = RGBColor(153, 171, 196)
CYAN = RGBColor(49, 203, 220)
GREEN = RGBColor(75, 213, 151)
ORANGE = RGBColor(255, 167, 67)
BLUE = RGBColor(78, 140, 245)
RED = RGBColor(245, 108, 120)
PURPLE = RGBColor(171, 126, 247)
FONT = "Microsoft YaHei"


def textbox(slide, x, y, w, h, text, size=10, color=WHITE, bold=False,
            align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, margin=0.04):
    shp = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shp.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return shp


def box(slide, x, y, w, h, text="", fill_color=PANEL_ALT, line=GRID,
        size=10, color=WHITE, bold=False, align=PP_ALIGN.CENTER,
        radius=True, lw=1.0):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    shp.line.color.rgb = line
    shp.line.width = Pt(lw)
    if text:
        tf = shp.text_frame
        tf.clear()
        tf.word_wrap = True
        tf.margin_left = Inches(0.06)
        tf.margin_right = Inches(0.06)
        tf.margin_top = Inches(0.02)
        tf.margin_bottom = Inches(0.02)
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


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=1.4, dashed=False):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = color
    ln.line.width = Pt(width)
    ln.line.end_arrowhead = True
    if dashed:
        ln.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return ln


def segment(slide, x1, y1, x2, y2, color=MUTED, width=1.4, dashed=False):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = color
    ln.line.width = Pt(width)
    if dashed:
        ln.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return ln


def section_title(slide, x, y, num, title, accent):
    box(slide, x, y, 0.31, 0.31, num, fill_color=accent, line=accent,
        size=10, color=BG, bold=True, radius=True, lw=0)
    textbox(slide, x + 0.40, y - 0.02, 3.8, 0.34, title, 12.5, WHITE, True)


def chip(slide, x, y, w, label, value, accent):
    box(slide, x, y, w, 0.55, "", fill_color=RGBColor(18, 36, 58), line=accent,
        radius=True, lw=1.0)
    textbox(slide, x + 0.08, y + 0.05, w - 0.16, 0.18, label, 7.7, MUTED, False,
            PP_ALIGN.LEFT)
    textbox(slide, x + 0.08, y + 0.23, w - 0.16, 0.24, value, 10.7, WHITE, True,
            PP_ALIGN.LEFT)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = BG

# Header
bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.32), Inches(0.24), Inches(0.065), Inches(0.68))
bar.fill.solid(); bar.fill.fore_color.rgb = CYAN; bar.line.fill.background()
textbox(slide, 0.50, 0.20, 8.8, 0.43,
        "AXI2CHI Order Buffer 模块设计方案与 PPA 权衡", 23, WHITE, True)
textbox(slide, 0.51, 0.64, 11.9, 0.30,
        "同 AWID 保序、不同 AWID 按 QoS 分流；以浅 Buffer 降低功耗与控制复杂度",
        10.4, MUTED)

# Column panels
box(slide, 0.30, 1.08, 4.87, 5.48, "", fill_color=PANEL, line=GRID, radius=True)
box(slide, 5.30, 1.08, 3.55, 5.48, "", fill_color=PANEL, line=GRID, radius=True)
box(slide, 8.98, 1.08, 4.05, 5.48, "", fill_color=PANEL, line=GRID, radius=True)

section_title(slide, 0.53, 1.25, "1", "架构与真实数据流", CYAN)
section_title(slide, 5.53, 1.25, "2", "关键机制", GREEN)
section_title(slide, 9.21, 1.25, "3", "参数选择与方案权衡", ORANGE)

# LEFT: AXI buffer architecture
box(slide, 0.55, 1.91, 0.82, 0.56, "AXI\nRequest", fill_color=RGBColor(22, 46, 74), line=BLUE,
    size=9.3, bold=True)
arrow(slide, 1.37, 2.19, 1.70, 2.19, CYAN)
box(slide, 1.70, 1.82, 1.18, 0.75, "AWID Match\n+ Channel Bind", fill_color=RGBColor(17, 54, 70), line=CYAN,
    size=9.3, bold=True)
textbox(slide, 1.66, 2.62, 1.30, 0.23, "same ID → same FIFO", 7.7, MUTED, False, PP_ALIGN.CENTER)

arrow(slide, 2.88, 2.06, 3.22, 1.84, ORANGE)
arrow(slide, 2.88, 2.34, 3.22, 2.60, BLUE)
box(slide, 3.22, 1.56, 1.38, 0.57, "HIGH FIFO  D=2", fill_color=RGBColor(100, 58, 23), line=ORANGE,
    size=9.4, bold=True)
box(slide, 3.22, 2.41, 1.38, 0.57, "LOW FIFO   D=2", fill_color=RGBColor(27, 61, 112), line=BLUE,
    size=9.4, bold=True)

# Route HIGH around the right edge to avoid crossing the LOW FIFO.
segment(slide, 4.60, 1.84, 4.78, 1.84, ORANGE)
segment(slide, 4.78, 1.84, 4.78, 3.53, ORANGE)
arrow(slide, 4.78, 3.53, 4.60, 3.53, ORANGE)
arrow(slide, 4.06, 2.98, 4.06, 3.24, BLUE)
box(slide, 3.53, 3.24, 1.07, 0.58, "2→1 QoS\nArbiter", fill_color=RGBColor(31, 53, 68), line=GREEN,
    size=9.2, bold=True)

box(slide, 0.62, 3.24, 1.22, 0.58, "Flow Control\nCredit / Ready", fill_color=RGBColor(34, 39, 61), line=PURPLE,
    size=8.6, bold=True)
arrow(slide, 1.84, 3.53, 3.53, 3.53, PURPLE, 1.2, dashed=True)

arrow(slide, 4.06, 3.82, 4.06, 4.11, GREEN)
box(slide, 3.31, 4.11, 1.50, 0.48, "CHI TXREQ", fill_color=RGBColor(24, 67, 57), line=GREEN,
    size=10.2, bold=True)

# Outstanding / response side
box(slide, 0.58, 4.37, 2.24, 1.14, "", fill_color=RGBColor(15, 46, 48), line=GREEN, radius=True)
textbox(slide, 0.73, 4.48, 1.94, 0.25, "Outstanding Linked List", 10.5, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, 0.73, 4.76, 1.94, 0.20, "AWID · next_ptr · is_head", 8.2, MUTED, False, PP_ALIGN.CENTER)
textbox(slide, 0.73, 5.00, 1.94, 0.27, "RXRSP乱序完成 / BRESP有序释放", 8.0, GREEN, False, PP_ALIGN.CENTER)

box(slide, 3.21, 4.79, 1.35, 0.48, "CHI RXRSP", fill_color=RGBColor(57, 42, 68), line=PURPLE,
    size=9.4, bold=True)
arrow(slide, 3.21, 5.03, 2.82, 5.03, PURPLE)
arrow(slide, 3.31, 4.35, 2.82, 4.66, GREEN, 1.2, dashed=True)
textbox(slide, 2.65, 4.23, 0.75, 0.20, "allocate/link", 7.2, GREEN, False, PP_ALIGN.CENTER)

box(slide, 0.67, 5.80, 1.20, 0.47, "CHI TXDAT", fill_color=RGBColor(34, 48, 67), line=MUTED,
    size=9.1, bold=True)
box(slide, 2.06, 5.80, 1.20, 0.47, "AXI BRESP", fill_color=RGBColor(34, 48, 67), line=MUTED,
    size=9.1, bold=True)
arrow(slide, 1.42, 5.51, 1.27, 5.80, GREEN)
arrow(slide, 2.10, 5.51, 2.66, 5.80, GREEN)

# CENTER: three mechanisms
box(slide, 5.55, 1.79, 3.05, 1.25, "", fill_color=RGBColor(16, 37, 58), line=CYAN, radius=True)
textbox(slide, 5.72, 1.87, 2.70, 0.22, "① AWID 粘滞分流", 10.5, CYAN, True)
box(slide, 5.72, 2.18, 0.70, 0.38, "NEW", fill_color=RGBColor(27, 50, 73), line=MUTED, size=8.2, bold=True)
arrow(slide, 6.42, 2.37, 6.78, 2.37, MUTED)
box(slide, 6.78, 2.15, 0.72, 0.44, "QoS", fill_color=RGBColor(61, 48, 31), line=ORANGE, size=8.8, bold=True)
arrow(slide, 7.50, 2.37, 7.83, 2.37, MUTED)
box(slide, 7.83, 2.15, 0.58, 0.44, "H/L", fill_color=RGBColor(27, 59, 90), line=BLUE, size=8.8, bold=True)
textbox(slide, 5.72, 2.67, 2.72, 0.21, "Active ID：忽略新 QoS，沿用绑定通道", 8.0, MUTED)

box(slide, 5.55, 3.18, 3.05, 1.34, "", fill_color=RGBColor(16, 40, 48), line=GREEN, radius=True)
textbox(slide, 5.72, 3.27, 2.70, 0.22, "② 事务生命周期", 10.5, GREEN, True)
states = [("ALLOC", CYAN), ("ISSUE", ORANGE), ("WAIT RSP", PURPLE), ("RELEASE", GREEN)]
sx = 5.72
for i, (name, accent_color) in enumerate(states):
    box(slide, sx, 3.70, 0.57 if i != 2 else 0.72, 0.42, name,
        fill_color=RGBColor(27, 43, 61), line=accent_color, size=7.5, bold=True)
    width = 0.57 if i != 2 else 0.72
    if i < len(states) - 1:
        arrow(slide, sx + width, 3.91, sx + width + 0.16, 3.91, MUTED, 1.0)
    sx += width + 0.18
textbox(slide, 5.72, 4.18, 2.72, 0.18, "entry 在 BRESP handshake 后释放", 7.8, MUTED)

box(slide, 5.55, 4.66, 3.05, 1.57, "", fill_color=RGBColor(27, 31, 49), line=PURPLE, radius=True)
textbox(slide, 5.72, 4.76, 2.70, 0.22, "③ 同 AWID 有序释放", 10.5, PURPLE, True)
box(slide, 5.72, 5.20, 0.52, 0.42, "HEAD", fill_color=RGBColor(52, 37, 67), line=PURPLE, size=7.5, bold=True)
arrow(slide, 6.24, 5.41, 6.48, 5.41, PURPLE)
box(slide, 6.48, 5.15, 0.56, 0.52, "A\ndone", fill_color=RGBColor(24, 67, 57), line=GREEN, size=7.8, bold=True)
arrow(slide, 7.04, 5.41, 7.28, 5.41, MUTED)
box(slide, 7.28, 5.15, 0.56, 0.52, "B\nwait", fill_color=RGBColor(55, 45, 38), line=ORANGE, size=7.8, bold=True)
arrow(slide, 7.84, 5.41, 8.08, 5.41, MUTED)
box(slide, 8.08, 5.15, 0.33, 0.52, "C", fill_color=RGBColor(32, 44, 62), line=MUTED, size=8.0, bold=True)
textbox(slide, 5.72, 5.80, 2.72, 0.21, "仅链头可释放；不同 AWID 可并行完成", 8.0, MUTED)

# RIGHT: key parameters
chip(slide, 9.23, 1.75, 0.82, "AWID", "11 bit", CYAN)
chip(slide, 10.13, 1.75, 0.82, "QoS", "1 bit", ORANGE)
chip(slide, 11.03, 1.75, 0.82, "FIFO", "2 × D2", GREEN)
chip(slide, 11.93, 1.75, 0.82, "ARB", "2 → 1", PURPLE)

textbox(slide, 9.23, 2.40, 3.45, 0.22, "axi_buffer 微架构比较", 9.3, WHITE, True)
cols = [0.85, 1.26, 1.35]
headers = ["指标", "双 FIFO ✓", "AWID 链表"]
for i, hdr in enumerate(headers):
    xx = 9.23 + sum(cols[:i])
    fc = RGBColor(28, 67, 60) if i == 1 else RGBColor(35, 47, 67)
    box(slide, xx, 2.69, cols[i], 0.38, hdr, fill_color=fc,
        line=GREEN if i == 1 else GRID, size=8.3, bold=True, radius=False)

rows = [
    ("QoS调度", "双通道", "逐链头"),
    ("High延迟", "D2：≤1项*", "更优"),
    ("Power", "较低", "较高"),
    ("Area", "较低", "中"),
    ("Complexity", "低", "高"),
    ("Robustness", "高", "中"),
]
rh = 0.37
for r, row in enumerate(rows):
    yy = 3.07 + r * rh
    for c, txt in enumerate(row):
        xx = 9.23 + sum(cols[:c])
        fc = RGBColor(16, 31, 50) if r % 2 == 0 else RGBColor(20, 36, 55)
        tc = GREEN if c == 1 and r >= 2 else (MUTED if c == 0 else WHITE)
        box(slide, xx, yy, cols[c], rh, txt, fill_color=fc, line=GRID,
            size=8.0, color=tc, bold=(c == 0), radius=False)

# PPA qualitative scatter/trend
textbox(slide, 9.23, 5.40, 3.45, 0.22, "PPA / 调度收益趋势（定性）", 9.3, WHITE, True)
plot_x, plot_y, plot_w, plot_h = 9.48, 5.74, 2.85, 0.58
arrow(slide, plot_x, plot_y + plot_h, plot_x + plot_w, plot_y + plot_h, MUTED, 1.0)
arrow(slide, plot_x, plot_y + plot_h, plot_x, plot_y, MUTED, 1.0)
textbox(slide, 10.40, 6.29, 1.85, 0.17, "Area / Power / Complexity →", 6.8, MUTED, False, PP_ALIGN.RIGHT)
textbox(slide, 9.12, 5.72, 0.32, 0.55, "调度\n灵活性", 6.6, MUTED, False, PP_ALIGN.CENTER)

# Trend arrow and points
arrow(slide, 9.75, 6.18, 11.95, 5.83, PURPLE, 1.2)
dual = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.90), Inches(6.02), Inches(0.15), Inches(0.15))
dual.fill.solid(); dual.fill.fore_color.rgb = GREEN; dual.line.color.rgb = GREEN
textbox(slide, 9.72, 5.78, 0.80, 0.20, "双 FIFO", 7.6, GREEN, True, PP_ALIGN.CENTER)
linked = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.60), Inches(5.75), Inches(0.15), Inches(0.15))
linked.fill.solid(); linked.fill.fore_color.rgb = PURPLE; linked.line.color.rgb = PURPLE
textbox(slide, 11.36, 5.92, 0.90, 0.20, "链表调度", 7.6, PURPLE, True, PP_ALIGN.CENTER)

# Footer decision banner
box(slide, 0.30, 6.70, 12.73, 0.56, "", fill_color=RGBColor(16, 54, 49), line=GREEN,
    radius=True, lw=1.4)
textbox(slide, 0.54, 6.79, 1.15, 0.24, "DESIGN CHOICE", 9.0, GREEN, True)
textbox(slide, 1.72, 6.76, 7.75, 0.30,
        "2×Depth-2 FIFO 做 QoS 调度  +  Linked List 做同 AWID 有序释放",
        12.0, WHITE, True)
textbox(slide, 9.45, 6.77, 3.30, 0.28,
        "低功耗/低复杂度优先；接受同 ID 临时 QoS 粘滞",
        8.6, MUTED, False, PP_ALIGN.RIGHT)

# Footnote
textbox(slide, 9.24, 6.40, 3.46, 0.18,
        "* ≤1项表示 FIFO 位置等待；实际周期受 credit / ready / 仲裁影响",
        6.9, MUTED)

prs.save(OUT)
print(OUT)
