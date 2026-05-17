import vapoursynth as vs

input_file = globals().get("input")
if not input_file:
    raise RuntimeError("Must give an input file using -a input=path")

factor = int(globals().get("factor", 2))

core = vs.core

import vsrife

clip = core.ffms2.Source(input_file)
clip = core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709")
clip = vsrife.rife(
    clip,
    factor_num=factor,
    trt=True,
    trt_optimization_level=5,
    auto_download=True
)
clip = core.resize.Bicubic(clip, format=vs.YUV420P8, matrix_s="709")

clip.set_output()