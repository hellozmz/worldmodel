from __future__ import annotations
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "lessons"

lessons = [
{
"num":"0001","slug":"mental-map","title":"建立世界模型与具身智能的心智地图","module":"Module A · Orientation",
"minutes":"15–20 分钟","goal":"能用一句话说清 world model、policy、VLA、dataset、benchmark、challenge 的边界。",
"body":"""
<section><h2>为什么这张地图重要</h2><p>世界模型和具身智能的论文经常混用“模型”两个字：有时指预测未来的 <b>world model</b>，有时指决策的 <b>policy</b>，有时指整个 <b>agent</b>。如果不先分清，你会把“能生成视频”误认为“能控制机器人”。</p>
<div class="grid">
<article class="card"><h3>World model</h3><p>学习 <code>(o,a)→o'</code>、<code>r</code>、<code>done</code> 或未来视频。它回答：如果我这么做，世界会怎样？</p></article>
<article class="card"><h3>Policy</h3><p>学习 <code>o→a</code>。它回答：我现在应该怎么做？</p></article>
<article class="card"><h3>VLA</h3><p>输入图像、语言、状态，输出动作块。通常是 policy，不必然显式预测未来。</p></article>
<article class="card"><h3>Embodied AI</h3><p>把感知、决策、动作和真实/仿真环境连成闭环。</p></article>
<article class="card"><h3>Benchmark / Challenge</h3><p>Benchmark 是固定协议；challenge 是按官方指标排名的比赛。先看指标，再看榜单。</p></article>
</div></section>
<section><h2>本课程使用的五个对象</h2><table><thead><tr><th>对象</th><th>本地代表</th><th>核心问题</th></tr></thead><tbody>
<tr><td>Video world model</td><td>Cosmos3-Nano</td><td>未来画面是否合理？</td></tr>
<tr><td>Latent world model</td><td>Tiny RSSM</td><td>低维状态能否预测未来？</td></tr>
<tr><td>VLA</td><td>SmolVLA</td><td>语言+图像+状态如何输出动作？</td></tr>
<tr><td>Dataset</td><td>LeRobot PushT</td><td>数据分布和 action 空间是什么？</td></tr>
<tr><td>Benchmark</td><td>gym-pusht</td><td>闭环 return / coverage / success 如何？</td></tr>
</tbody></table></section>
<section><h2>实践：三分钟分类训练</h2><ol><li>打开 <a href="../reference/basic-introduction.html">基本介绍</a> 和 <a href="../reference/field-map.html">Field Map</a>。</li><li>把 Cosmos、RSSM、SmolVLA、PushT 数据集、gym-pusht 分别写在纸上。</li><li>给每个对象标注：输入、输出、是否显式预测未来、是否直接输出动作。</li><li>检查你是否能说出每个对象的证据等级：interface / offline / closed-loop。</li><li>用一句话说明 benchmark、leaderboard、challenge 的差别，再查看 <a href="../reference/benchmark-map.html">比赛与 Benchmark 地图</a>。</li></ol>
<div class="callout blue"><strong>小胜利</strong><p>完成后，你应该能把“会预测”和“会行动”分成两条线，并知道它们可以组合。</p></div></section>
""",
"source":"DreamerV3 与 Cosmos 是理解两条主线的起点：<a href='https://www.nature.com/articles/s41586-025-08744-2' target='_blank'>DreamerV3</a>、<a href='https://arxiv.org/abs/2501.03575' target='_blank'>Cosmos</a>。",
"quiz":{"q":"SmolVLA 输出 action chunk 时，最准确的分类是什么？","opts":[("Vision-Language-Action policy","false"),("Generative video model","false"),("Latent dynamics model","false"),("Robot benchmark dataset","false")],"answer":0,"exp":"SmolVLA 的公开接口是把图像、语言和状态映射为动作块，因此是 VLA policy；它不显式输出未来画面。"},
"artifacts":[("Basic intro","../reference/basic-introduction.html"),("Benchmark map","../reference/benchmark-map.html")],
},
{
"num":"0002","slug":"pusht-dataset","title":"读懂一个机器人数据集：LeRobot PushT","module":"Module B · Data",
"minutes":"20 分钟","goal":"能解释 PushT 的字段、规模、单位和 episode 结构。",
"body":"""
<section><h2>先看数据，再看模型</h2><p>PushT 是一个二维推动任务：agent 要把 T 形块推到 T 形目标上。这个任务简单到可以快速实验，又包含了接触、遮挡和目标条件。</p>
<div class="grid"><article class="card"><h3>25,650 帧</h3><p>总观测-动作样本。</p></article><article class="card"><h3>206 episodes</h3><p>完整轨迹，不是独立图片。</p></article><article class="card"><h3>10 fps</h3><p>相邻帧高度相关。</p></article><article class="card"><h3>state/action 都是 2 维</h3><p>对应平面坐标，单位是像素空间。</p></article></div></section>
<section><h2>实践：读 schema</h2><pre><code>ssh h200_1727
docker exec -it zmz_dev_v2 bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/analyze_pusht.py</code></pre>
<p>打开 <code>analysis/pusht_summary.json</code>，找到：<code>observation.state</code>、<code>action</code>、<code>episode_index</code>、<code>next.success</code>。</p></section>
<section><h2>观察关键帧</h2><figure><img src="../source/worldmodel_embodied_ai/04_lerobot_dataset/analysis/episode0_contact_sheet.png" alt="PushT contact sheet"><figcaption>Contact sheet：看接触、遮挡和目标变化，而不是只看统计均值。</figcaption></figure></section>
<section><h2>你要掌握的三个判断</h2><ol><li>这个数据集是轨迹数据，不是独立同分布图片。</li><li>动作是绝对像素位置，不是关节角。</li><li>判断成功必须看 <code>next.success</code> / coverage，不能只看 loss。</li></ol></section>
""",
"source":"本地数据来自 <a href='https://huggingface.co/datasets/lerobot/pusht' target='_blank'>lerobot/pusht</a>；代码框架见 <a href='https://github.com/huggingface/lerobot' target='_blank'>LeRobot</a>。",
"quiz":{"q":"为什么训练/验证必须按 episode 切分？","opts":[("相邻帧高度相关","true"),("模型参数太多","false"),("图像分辨率太低","false"),("奖励函数太稀疏","false")],"answer":0,"exp":"同一 episode 的相邻帧几乎重复，随机按帧切分会把近似样本同时放进训练和验证，造成泄漏。"},
"artifacts":[("Dataset lab","../reference/pusht-lab.html")],
},
{
"num":"0003","slug":"baseline-leakage","title":"设计不泄漏的 baseline 和验证集","module":"Module B · Data",
"minutes":"20 分钟","goal":"能用 baseline 判断模型是否真的学到结构，而不是被指标骗了。",
"body":"""
<section><h2>为什么需要 baseline</h2><p>一个模型看起来 loss 很低，可能只是因为动作变化平滑。没有 baseline，你无法判断它学到的是不是“重复上一帧/上一动作”这种浅层规律。</p>
<div class="grid"><article class="card"><h3>action = state</h3><p>最简单的位置先验。</p></article><article class="card"><h3>action = train mean</h3><p>只猜全局均值。</p></article><article class="card"><h3>action = previous action</h3><p>惯性/平滑性 baseline。</p></article></div></section>
<section><h2>本地结果</h2><table><thead><tr><th>Baseline</th><th>MSE</th></tr></thead><tbody><tr><td>action = state</td><td>404.84</td></tr><tr><td>action = train mean</td><td>9778.39</td></tr><tr><td>action = previous action</td><td>91.06</td></tr><tr><td>Tiny MLP validation</td><td>等效 RMSE 19.29px/维</td></tr></tbody></table><p>tiny policy 明显优于这些 baseline，但这仍只是 offline 证据。</p></section>
<section><h2>实践：写一个假想实验</h2><ol><li>假设你把 episode 0 的前 80% 作为训练，后 20% 作为验证。</li><li>写出可能泄漏的原因。</li><li>比较 random split 和 episode split 的验证 MSE。</li><li>解释为什么后者更可信。</li></ol><div class="callout warn"><strong>关键红线</strong><p>同一 episode 不能同时出现在训练和验证。</p></div></section>
""",
"source":"最佳实践来自本课程实验记录与 <a href='https://github.com/huggingface/lerobot' target='_blank'>LeRobot 数据组织方式</a>。",
"quiz":{"q":"如果随机按帧切分，最直接的问题是什么？","opts":[("验证集被污染","true"),("训练速度变慢","false"),("显存占用翻倍","false"),("标签数量减少","false")],"answer":0,"exp":"相邻帧几乎相同，随机切分会让验证集包含训练样本的近似副本。"},
"artifacts":[("PushT lab","../reference/pusht-lab.html")],
},
{
"num":"0004","slug":"cosmos-video","title":"视频世界模型：让模型想象未来","module":"Module C · Video world models",
"minutes":"20–25 分钟","goal":"理解 Cosmos T2V 的输入、输出和物理一致性评估。",
"body":"""
<section><h2>视频世界模型在做什么</h2><p>给定 prompt，模型生成一段未来可能的视频。它不是在求唯一正确答案，而是在学习一个合理的未来分布。</p>
<div class="grid"><article class="card"><h3>T2V</h3><p>从文本想象场景。</p></article><article class="card"><h3>I2V</h3><p>给定当前帧预测未来。</p></article><article class="card"><h3>Action conditioning</h3><p>当前画面 + 动作序列 → 未来画面。</p></article><article class="card"><h3>Reasoner / policy</h3><p>同一基础模型可以扩展到规划与动作。</p></article></div></section>
<section><h2>实践：看本地生成结果</h2><figure><video controls src="../cosmos3_nano_worldmodel_tutorial/outputs/worldmodel_t2v_20261024_192234.mp4"></video><figcaption>448×256、25 帧、12fps。观察相机运动、遮挡、阴影和物体稳定性。</figcaption></figure>
<p>打开 <code>outputs/worldmodel_t2v_20261024_192234_request.json</code>，找到 <code>prompt</code>、<code>num_frames</code>、<code>guidance_scale</code>、<code>seed</code>。</p></section>
<section><h2>评估三件事</h2><ol><li><b>时间一致性：</b>物体是否突然消失或变形？</li><li><b>物理合理性：</b>阴影、遮挡、碰撞是否符合直觉？</li><li><b>可控性：</b>改 prompt 或 action 后，画面是否按预期变化？</li></ol><div class="callout"><strong>边界</strong><p>视频漂亮说明生成能力强，不等于它能稳定用于控制。</p></div></section>
""",
"source":"一手资料：<a href='https://arxiv.org/abs/2501.03575' target='_blank'>NVIDIA Cosmos 论文</a>；可对比 <a href='https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models' target='_blank'>Genie 3</a>。",
"quiz":{"q":"视频世界模型最核心的输出是什么？","opts":[("未来画面分布","true"),("最优动作序列","false"),("奖励函数参数","false"),("数据集标注结果","false")],"answer":0,"exp":"它的核心是预测未来观测；动作输出属于 policy 或 action-conditioning 扩展，不是 T2V 本身。"},
"artifacts":[],
},
{
"num":"0005","slug":"video-latent","title":"从像素到 latent：视频生成组件拆解","module":"Module C · Video world models",
"minutes":"20 分钟","goal":"能把 VAE、diffusion/flow、Transformer attention 对应到视频生成流程。",
"body":"""
<section><h2>为什么要压缩到 latent</h2><p>直接在像素上做长视频注意力太贵。常见做法是先用 VAE 把视频压成 latent，再在 latent 空间去噪，最后解码回像素。</p>
<pre><code>prompt → text tokenizer
video → VAE encoder → latent
noise + latent + condition → DiT / diffusion / flow
denoised latent → VAE decoder → MP4</code></pre></section>
<section><h2>三个组件</h2><div class="grid"><article class="card"><h3>VAE</h3><p>学习像素和 latent 的双向映射。</p></article><article class="card"><h3>Diffusion / flow</h3><p>从噪声逐步走向数据分布。</p></article><article class="card"><h3>Transformer attention</h3><p>建模时间和空间依赖。</p></article></div></section>
<section><h2>实践：组件排序</h2><p>打开本地 <code>cosmos3_nano_worldmodel_tutorial/model/model_index.json</code>（如有远端权限则在 H200 上查看），列出 pipeline 组件。然后把下面流程排序：</p><ol><li>VAE decoder</li><li>text tokenizer</li><li>latent 去噪</li><li>MP4 封装</li></ol><p>正确顺序应为：2 → 3 → 1 → 4。</p></section>
<section><h2>和 RSSM 的联系</h2><p>Cosmos 在像素/latent 视频空间预测；RSSM 在更低维状态 latent 中预测。前者适合想象，后者更适合控制和 RL。</p></section>
""",
"source":"阅读 <a href='https://arxiv.org/abs/2501.03575' target='_blank'>Cosmos 论文</a> 的模型结构部分；后续可对比 <a href='https://arxiv.org/abs/2506.09985' target='_blank'>V-JEPA 2</a>。",
"quiz":{"q":"VAE 在视频生成中的主要作用是什么？","opts":[("压缩并表示视频","true"),("选择最优策略","false"),("计算环境奖励","false"),("切分训练数据","false")],"answer":0,"exp":"VAE 负责像素和 latent 的映射，降低后续生成模型的计算负担。"},
"artifacts":[("Frontier map","../reference/frontier-map.html")],
},
{
"num":"0006","slug":"rssm-training","title":"训练一个 RSSM 式 latent world model","module":"Module D · Latent world models",
"minutes":"25 分钟","goal":"能说清 posterior、prior、GRU、decoder、KL 各自的作用。",
"body":"""
<section><h2>Dreamer 的关键思想</h2><p>不要在像素上直接学习全部动态，而是学习一个紧凑 latent state，再在这个 latent 空间里想象未来并训练策略。</p>
<pre><code>posterior: q(z_t | o_t, h_t)
prior:     p(z_t | h_t)
recurrent: h_t = GRU(z_t, a_t, h_t)
decode:    z_t → o_t, r_t, done_t
loss:      reconstruction + reward + done + KL</code></pre></section>
<section><h2>本地教学模型</h2><table><thead><tr><th>项</th><th>值</th></tr></thead><tbody><tr><td>hidden</td><td>128</td></tr><tr><td>latent</td><td>16</td></tr><tr><td>sequence length</td><td>32</td></tr><tr><td>steps</td><td>1200</td></tr><tr><td>val loss</td><td>0.25721</td></tr><tr><td>val obs MSE</td><td>0.04346</td></tr></tbody></table></section>
<section><h2>实践：跑训练</h2><pre><code>ssh h200_1727
docker exec -it zmz_dev_v2 bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/02_dreamer_latent_rl
source ../04_lerobot_dataset/.venv/bin/activate
python scripts/train_tiny_worldmodel.py --steps 1200</code></pre>
<p>观察 loss、obs MSE、KL 是否同时下降或进入平衡。</p></section>
<section><h2>读图</h2><figure><img src="../source/worldmodel_embodied_ai/02_dreamer_latent_rl/outputs/worldmodel_loss_curve.png" alt="RSSM loss curve"><figcaption>训练诊断：如果 KL 塌缩，decoder 可能失去信息。</figcaption></figure></section>
""",
"source":"一手资料：<a href='https://www.nature.com/articles/s41586-025-08744-2' target='_blank'>DreamerV3</a>；代码参考 <a href='https://github.com/danijar/dreamerv3' target='_blank'>官方实现</a>。",
"quiz":{"q":"RSSM 中 prior 的作用是什么？","opts":[("无观测时预测","true"),("压缩当前图像","false"),("解码奖励信号","false"),("归一化动作数值","false")],"answer":0,"exp":"prior 只依赖 recurrent state，在想象阶段没有真实观测时用来预测 latent。"},
"artifacts":[("RSSM notebook","../reference/rssm-notebook.html")],
},
{
"num":"0007","slug":"open-loop-rollout","title":"诊断 open-loop rollout 的误差累积","module":"Module D · Latent world models",
"minutes":"20 分钟","goal":"能区分 teacher-forced loss 和想象 rollout 的可靠性。",
"body":"""
<section><h2>两种预测方式</h2><div class="grid"><article class="card"><h3>Teacher forcing</h3><p>每一步都给真实观测，训练稳定，但可能掩盖误差累积。</p></article><article class="card"><h3>Open-loop / imagination</h3><p>用模型自己的预测继续往前走，更接近真实使用场景。</p></article></div></section>
<section><h2>本地结果</h2><p>tiny RSSM 的验证 obs MSE 是 0.04346，但 64 步 open-loop rollout MSE 达到 212.97 px/coordinate。这个差距正是误差累积。</p></section>
<section><h2>实践：读 rollout 图</h2><figure><img src="../source/worldmodel_embodied_ai/02_dreamer_latent_rl/outputs/worldmodel_rollout.png" alt="RSSM rollout"><figcaption>观察预测曲线何时开始偏离，以及哪个坐标更不稳定。</figcaption></figure>
<ol><li>找出第一个明显偏离的步数。</li><li>判断是 x 还是 y 更难预测。</li><li>提出一个改进：更长序列、动作归一化、更大 latent，还是加入图像观测？</li></ol></section>
<section><h2>关键结论</h2><div class="callout warn"><strong>不要只报 val loss</strong><p>world model 必须报告 open-loop horizon 和误差曲线，否则无法判断能否用于想象训练。</p></div></section>
""",
"source":"参考 <a href='https://www.nature.com/articles/s41586-025-08744-2' target='_blank'>DreamerV3</a> 中的 imagination 训练。",
"quiz":{"q":"Open-loop rollout 的主要风险是什么？","opts":[("误差逐步累积","true"),("数据标签缺失","false"),("动作维度过高","false"),("随机种子不可用","false")],"answer":0,"exp":"模型把自己的预测当作下一步输入，小误差会随时间放大。"},
"artifacts":[("RSSM notebook","../reference/rssm-notebook.html")],
},
{
"num":"0008","slug":"imitation-policy","title":"训练一个小型 imitation policy","module":"Module E · Policies",
"minutes":"25 分钟","goal":"能解释 state→action MLP 的训练、归一化和验证指标。",
"body":"""
<section><h2>任务定义</h2><p>给当前 agent 位置 <code>s∈R²</code>，预测动作 <code>a∈R²</code>。模型是 <code>2→256→256→2</code> 的 MLP。</p>
<div class="grid"><article class="card"><h3>Normalization</h3><p>state 和 action 都用训练集均值/方差归一化。</p></article><article class="card"><h3>Episode split</h3><p>165 train / 41 validation。</p></article><article class="card"><h3>训练</h3><p>300 epochs，AdamW + cosine schedule。</p></article><article class="card"><h3>验证</h3><p>normalized MSE 0.03817。</p></article></div></section>
<section><h2>实践：跑 policy</h2><pre><code>ssh h200_1727
docker exec -it zmz_dev_v2 bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/train_tiny_policy.py</code></pre></section>
<section><h2>读预测图</h2><figure><img src="../source/worldmodel_embodied_ai/04_lerobot_dataset/outputs/tiny_policy_predictions.png" alt="Tiny policy predictions"><figcaption>观察预测是否只学会平滑轨迹，还是能跟住转折。</figcaption></figure></section>
<section><h2>边界</h2><p>这个模型没有看到 goal pose 和 block pose，因此不可能完整解决 PushT。它是 baseline，不是最终方案。</p></section>
""",
"source":"数据来自 <a href='https://huggingface.co/datasets/lerobot/pusht' target='_blank'>PushT</a>；训练框架见 <a href='https://github.com/huggingface/lerobot' target='_blank'>LeRobot</a>。",
"quiz":{"q":"这个 tiny policy 最重要的信息缺失是什么？","opts":[("目标块状态","true"),("训练轮数不足","false"),("显存容量不足","false"),("文本提示缺失","false")],"answer":0,"exp":"仅用 agent 位置无法推断 T 块目标；policy 缺少关键任务状态。"},
"artifacts":[("PushT lab","../reference/pusht-lab.html")],
},
{
"num":"0009","slug":"closed-loop","title":"闭环评估：offline 好不等于任务成功","module":"Module E · Policies",
"minutes":"25 分钟","goal":"能解释 return、coverage、success rate 和 offline metric 的差别。",
"body":"""
<section><h2>为什么必须闭环</h2><p>离线预测中，每一步输入都来自数据集；闭环中，模型自己的动作会改变未来观测。分布会漂移，小错误会累积。</p></section>
<section><h2>本地结果</h2><table><thead><tr><th>Policy</th><th>Success</th><th>Mean return</th><th>Final coverage</th></tr></thead><tbody><tr><td>Random</td><td>0/10</td><td>1.624</td><td>0.000</td></tr><tr><td>Tiny imitation</td><td>0/10</td><td>12.728</td><td>0.00815</td></tr></tbody></table><p>tiny policy 在 return/coverage 上优于随机，但严格成功率仍为 0。</p></section>
<section><h2>实践：比较两个视频</h2><div class="grid"><figure><video controls src="../source/worldmodel_embodied_ai/05_simulation_benchmarks/outputs/pusht_random.mp4"></video><figcaption>Random policy</figcaption></figure><figure><video controls src="../source/worldmodel_embodied_ai/05_simulation_benchmarks/outputs/pusht_tiny_policy.mp4"></video><figcaption>Tiny imitation policy</figcaption></figure></div>
<ol><li>找出 tiny policy 更稳定的行为。</li><li>指出它仍然失败的原因。</li><li>写一个改进假设，例如加入 block pose / goal pose / image。</li></ol></section>
<section><h2>结论模板</h2><div class="callout good"><strong>正确表述</strong><p>“Tiny policy improves return and coverage over random but does not solve PushT.”</p></div></section>
<section><h2>实践：套用评价体系</h2><p>打开 <a href="../reference/evaluation-system.html">评价体系</a>，把本实验填入三级证据阶梯，并写出每个数字“能证明什么 / 不能证明什么”。</p></section>
""",
"source":"评估环境：gym-pusht；数据：<a href='https://huggingface.co/datasets/lerobot/pusht' target='_blank'>lerobot/pusht</a>。",
"quiz":{"q":"Closed-loop evaluation 的关键特征是什么？","opts":[("动作改变未来","true"),("数据完全随机","false"),("奖励必须为零","false"),("模型无需环境","false")],"answer":0,"exp":"闭环中策略的动作影响后续观测，因此会暴露复合误差和分布漂移。"},
"artifacts":[("Evaluation system","../reference/evaluation-system.html")],
},
{
"num":"0010","slug":"smolvla-interface","title":"SmolVLA：检查一个 VLA 接口","module":"Module F · VLA",
"minutes":"25 分钟","goal":"能解释 action chunk、flow matching 和 VLA 的输入输出。",
"body":"""
<section><h2>SmolVLA 在做什么</h2><p>SmolVLA 把图像、机器人状态和任务语言映射为动作块。它不是先生成完整未来视频再规划，而是直接输出动作。</p>
<pre><code>observation.images.camera1
observation.state
task text
        ↓
   SmolVLA
        ↓
action chunk: (1, 50, 6)</code></pre></section>
<section><h2>本地 GPU 结果</h2><table><thead><tr><th>项</th><th>值</th></tr></thead><tbody><tr><td>参数</td><td>450M</td></tr><tr><td>首次推理</td><td>491ms</td></tr><tr><td>warmed-up</td><td>约 145ms</td></tr><tr><td>显存</td><td>1.25GB</td></tr></tbody></table></section>
<section><h2>实践：读 JSON</h2><p>打开 <code>source/worldmodel_embodied_ai/03_vla_smolvla/outputs/smolvla_gpu_metrics.json</code>，找出：</p><ol><li>input state shape</li><li>output shape</li><li>first run vs repeat timings</li><li>GPU memory</li></ol></section>
<section><h2>Flow matching 直觉</h2><p>不是输出唯一动作均值，而是学习从噪声分布移动到动作分布的路径，因此能表示多模态行为。</p></section>
""",
"source":"一手资料：<a href='https://arxiv.org/abs/2506.01844' target='_blank'>SmolVLA 论文</a>；对比 <a href='https://arxiv.org/abs/2410.24164' target='_blank'>π0</a>。",
"quiz":{"q":"Action chunk 的直接优点是什么？","opts":[("减少推理次数","true"),("消除动作噪声","false"),("保证任务成功","false"),("替代环境仿真","false")],"answer":0,"exp":"一次输出多步动作可以降低推理频率，并保留短时序结构；但它不保证成功。"},
"artifacts":[("VLA notebook","../reference/vla-notebook.html")],
},
{
"num":"0011","slug":"embodiment-mismatch","title":"发现 embodiment mismatch","module":"Module F · VLA",
"minutes":"20 分钟","goal":"能判断一个 VLA 结果能否跨机器人/任务外推。",
"body":"""
<section><h2>问题</h2><p>本地 SmolVLA 实验把 PushT 的 2 维 state pad 到 6 维，并把 PushT 图像作为 camera1。这能让张量形状跑通，但不能说明模型理解了 PushT。</p>
<div class="grid"><article class="card"><h3>维度不同</h3><p>PushT action 是 2 维，SmolVLA 输出 6 维。</p></article><article class="card"><h3>物理含义不同</h3><p>像素平面位置 ≠ 关节/夹爪动作。</p></article><article class="card"><h3>数据分布不同</h3><p>SmolVLA 的训练 embodiment 与 PushT 不一致。</p></article></div></section>
<section><h2>三种处理方式</h2><ol><li><b>不处理：</b>只作为 interface smoke test。</li><li><b>Adapter：</b>显式映射状态/动作，但必须说明假设。</li><li><b>Finetune + closed-loop eval：</b>在匹配数据上微调，再用仿真/真机验证。</li></ol></section>
<section><h2>实践：判断结论能否外推</h2><p>阅读以下句子，标出能否成立：</p><ul><li>“SmolVLA 在本地 GPU 上能输出 (1,50,6)。” <b>能成立。</b></li><li>“SmolVLA 已学会 PushT。” <b>不能成立。</b></li><li>“SmolVLA 可用于 PushT 控制。” <b>需要 finetune/adapter 和闭环验证。</b></li></ul></section>
<section><h2>一手资料</h2><p>比较 <a href='https://arxiv.org/abs/2307.15818' target='_blank'>RT-2</a>、<a href='https://arxiv.org/abs/2406.09246' target='_blank'>OpenVLA</a> 和 <a href='https://arxiv.org/abs/2506.01844' target='_blank'>SmolVLA</a> 如何定义 embodiment 与数据分布。</p></section>
""",
"source":"VLA 跨 embodiment 的核心约束来自各自论文的训练数据与动作空间定义。",
"quiz":{"q":"本实验为什么不能声称 SmolVLA 学会了 PushT？","opts":[("动作空间不匹配","true"),("GPU 数量不足","false"),("提示词太短","false"),("视频帧率过高","false")],"answer":0,"exp":"PushT 是 2 维平面动作，而 SmolVLA 输出 6 维动作；接口通过 padding 跑通，不等于语义匹配。"},
"artifacts":[("VLA notebook","../reference/vla-notebook.html")],
},
{
"num":"0012","slug":"capstone","title":"设计你的 world model + embodied AI capstone","module":"Module G · Integration",
"minutes":"30–40 分钟","goal":"能写出一页可执行、可证伪的实验设计。",
"body":"""
<section><h2>把课程串起来</h2><p>一个好的具身智能实验必须同时说明：<b>世界模型</b>、<b>策略</b>、<b>数据</b>、<b>评估</b>和<b>失败判据</b>。</p></section>
<section><h2>Capstone 模板</h2><pre><code>1. Hypothesis: 加入 block pose + goal pose 会降低 PushT 闭环误差
2. Model: state(s, block, goal) → action; 或 RSSM + policy
3. Baselines: random / previous action / tiny MLP
4. Data split: episode-safe 80/20
5. Offline metric: action MSE / rollout MSE
6. Closed-loop metric: return, coverage, success rate
7. Failure criterion: 若 success 不提升或 coverage 下降，则假设失败
8. Compute: 1×H200, 预算 1 小时
9. Evidence: JSON + PNG + MP4 + command</code></pre></section>
<section><h2>三个可选方向</h2><div class="grid"><article class="card"><h3>A. richer-state policy</h3><p>把 block pose 和 goal pose 加入 tiny MLP。</p></article><article class="card"><h3>B. image policy</h3><p>用 PushT 图像替代 2 维 state。</p></article><article class="card"><h3>C. world-model planning</h3><p>用 RSSM rollout 候选动作，选择高价值动作。</p></article></div></section>
<section><h2>实践：写一页实验设计</h2><ol><li>选择一个方向。</li><li>写出 hypothesis 和 null result。</li><li>列出输入/输出张量。</li><li>列出至少两个 baseline。</li><li>说明如何避免泄漏。</li><li>定义成功和失败阈值。</li></ol><div class="callout good"><strong>完成标准</strong><p>别人只看你的设计，就能复现实验并判断结果是否支持假设。</p></div></section>
<section><h2>实践：选择外部 Benchmark</h2><p>打开 <a href="../reference/benchmark-map.html">比赛与 Benchmark 地图</a>，根据你的方向选择一个下一步平台，并说明任务族、指标、算力和提交要求。</p></section>
""",
"source":"综合参考：<a href='https://www.nature.com/articles/s41586-025-08744-2' target='_blank'>DreamerV3</a>、<a href='https://arxiv.org/abs/2506.01844' target='_blank'>SmolVLA</a>、<a href='https://arxiv.org/abs/2501.03575' target='_blank'>Cosmos</a>。",
"quiz":{"q":"一个 capstone 设计最不可缺少的是什么？","opts":[("可证伪判据","true"),("更大模型","false"),("更多论文","false"),("更长训练","false")],"answer":0,"exp":"没有失败判据，结果无法被科学评估；模型规模和训练时长只是手段。"},
"artifacts":[("Field map","../reference/field-map.html"),("Frontier map","../reference/frontier-map.html"),("Evaluation system","../reference/evaluation-system.html"),("Benchmark map","../reference/benchmark-map.html")],
},
{
"num":"0013","slug":"roboworld-output","title":"RoboWorld 2026：把课程学习变成参赛产出","module":"Module H · Target Output",
"minutes":"30–45 分钟","goal":"能把前 12 课的方法训练转化为一个明确的 RoboWorld 项目包和提交计划。",
"body":"""
<section><h2>为什么要有目标活动</h2><p>只学习概念容易停在“我看过论文、跑过 demo”。一个明确的外部产出会迫使你回答更实际的问题：任务是什么、指标是什么、baseline 在哪里、我的改进是否真的有效、别人能否复现。</p>
<div class="callout blue"><strong>本课程选择</strong><p>主目标采用 <b>RoboWorld Challenge 2026 · WorldNav</b>：单张初始 RGB 图像和自然语言指令输入，输出完整未来导航轨迹。它同时覆盖 language grounding、world model、policy 和 trajectory evaluation，和课程主线最一致。</p></div></section>
<section><h2>三个赛道的取舍</h2><table><thead><tr><th>Track</th><th>定位</th><th>为什么选 / 不选</th></tr></thead><tbody>
<tr><td>WorldNav</td><td><b>主目标</b></td><td>任务形式与课程最贴近：vision + language → future trajectory；允许 world model、VLA 和 policy-only 方法。</td></tr>
<tr><td>HA-VLN 2.0</td><td><b>进阶目标</b></td><td>闭环 RGB-D 导航、动态行人和 social compliance 很有价值，但系统复杂度更高。</td></tr>
<tr><td>SafeDrive-VLA</td><td><b>观察目标</b></td><td>world-model dreaming 与安全冲突很有启发，但训练数据约 1.2TB，不适合作为第一参赛目标。</td></tr>
</tbody></table>
<p>完整对比见 <a href="../reference/roboworld-2026.html">RoboWorld 2026 参考页</a>。</p></section>
<section><h2>课程能力如何迁移</h2><div class="grid">
<article class="card"><h3>从 Cosmos 迁移</h3><p>关注 future observation prediction 是否能帮助选择动作，而不是只生成好看的视频。</p></article>
<article class="card"><h3>从 RSSM 迁移</h3><p>用 rollout error vs horizon 检验想象稳定性，避免只看 teacher-forced loss。</p></article>
<article class="card"><h3>从 SmolVLA 迁移</h3><p>审计 action chunk、单位、坐标系、Stop 语义和 embodiment，不把接口跑通当作任务掌握。</p></article>
<article class="card"><h3>从 PushT 迁移</h3><p>把 episode-safe split、baseline、offline/closed-loop 证据阶梯带到官方数据审计。</p></article>
</div></section>
<section><h2>产出路线</h2><pre><code>P0 Decision       阅读规则、注册、确认算力/存储、选择 WorldNav
P1 Reproduce       审计 schema、下载最小子集、复现 baseline
P2 Improve         只加入一个明确组件：语言编码 / 轨迹解码 / latent rollout / VLA adapter
P3 Validate        在 seen + unseen validation 上报告 SR、ATE、RPE、route fidelity
P4 Submit          生成官方格式预测、记录分数变化、写技术报告
P5 Archive         固化配置、seed、命令、失败案例和下一版计划</code></pre>
<p>项目目录模板和详细检查表见 <code>ROBOWORLD_2026_PLAN.md</code>。</p></section>
<section><h2>实践：写你的参赛立项页</h2><ol><li>创建 <code>roboworld_2026/README.md</code>。</li><li>写下团队、主赛道、方法路线和第一个 baseline。</li><li>列出输入张量、输出张量、单位和官方指标。</li><li>定义 P0–P5 里程碑和每阶段的可交付文件。</li><li>写出风险：数据下载、算力、动作空间、 unseen 泛化、提交格式。</li><li>明确失败判据：什么结果说明该组件没有价值。</li></ol>
<div class="callout good"><strong>完成标准</strong><p>队友只读你的 README 和 <code>run.sh</code>，就能复现数据审计、baseline、validation 和提交文件生成流程。</p></div></section>
<section><h2>证据边界</h2><ul><li>PushT 是二维 manipulation，WorldNav 是语言条件导航；本地结果不能预测官方排名。</li><li>WorldNav 是 open-loop trajectory evaluation；HA-VLN 才提供更强的闭环交互评估。</li><li>官方页面当前只列时间线阶段，报名和提交前必须核对当届具体日期和规则。</li><li>比赛排名是外部结果；课程产出以可复现实验、清晰报告和失败分析为准。</li></ul></section>
""",
"source":"官方信息见 <a href='https://roboworld2026.github.io' target='_blank'>RoboWorld Challenge 2026</a>、<a href='https://roboworld2026.github.io/track1.html' target='_blank'>WorldNav</a>、<a href='https://roboworld2026.github.io/track2.html' target='_blank'>HA-VLN 2.0</a>、<a href='https://roboworld2026.github.io/track3.html' target='_blank'>SafeDrive-VLA</a>。",
"quiz":{"q":"什么才算本课程面向 RoboWorld 的有效产出？","opts":[("可复现项目包、验证结果和失败分析","true"),("只提交一次排行榜分数","false"),("只写一份想法文档","false"),("只跑通模型下载","false")],"answer":0,"exp":"有效产出的核心是可复现性和证据链：官方指标、baseline、消融、失败案例、提交记录和报告共同构成完整证据。"},
"artifacts":[("RoboWorld 2026","../reference/roboworld-2026.html"),("Evaluation system","../reference/evaluation-system.html"),("Benchmark map","../reference/benchmark-map.html")],
},
{
"num":"0014","slug":"research-portfolio","title":"从课程到研究组合：比赛、论文与 Benchmark 三条产出线","module":"Module I · Research Portfolio",
"minutes":"35–50 分钟","goal":"能把同一套实验能力规划成 challenge、workshop paper/technical report 或 benchmark reproduction 三条可并行退出的产出线。",
"body":"""
<section><h2>为什么不要只押一个比赛</h2><p>RoboWorld WorldNav 仍然是本课程的默认 challenge 路线，但它不是唯一出口。比赛有报名窗口、资格规则、数据体量和提交格式的不确定性；如果把学习目标完全绑定在一个外部时间表上，规则变化或截稿错过会让成果没有落点。</p>
<div class="callout blue"><strong>研究组合思维</strong><p>把已有实验拆成三个互相复用的出口：<b>Challenge</b> 面向官方指标和排名，<b>Workshop paper / technical report</b> 面向问题和证据链，<b>Benchmark / reproduction report</b> 面向协议、baseline 和复现性。它们共享数据审计、实验代码和失败分析。</p></div></section>
<section><h2>三条产出线怎么选</h2><table><thead><tr><th>产出线</th><th>核心问题</th><th>最低证据</th><th>适合时机</th></tr></thead><tbody>
<tr><td>Challenge submission</td><td>官方指标是否提高？提交格式是否合法？</td><td>官方 baseline、validation 提交、规则记录、分数日志</td><td>官方窗口仍在，且数据/算力可承受</td></tr>
<tr><td>Workshop paper / technical report</td><td>研究问题是否清晰？结果能否解释？</td><td>多 baseline、多 seed、消融、seen/unseen、失败分析</td><td>有一个可检验假设，即使结果为负也有价值</td></tr>
<tr><td>Benchmark / reproduction report</td><td>别人能否复现？边界在哪里？</td><td>协议、环境、配置、命令、表格、误差来源</td><td>算力有限，或官方活动已过窗口</td></tr>
</tbody></table>
<div class="callout"><strong>优先级建议</strong><p>第一层先把 PushT/RSSM/VLA 实验整理成可复现记录；第二层选择一个 challenge 作为外部压力测试；第三层把最稳定的问题沉淀成 workshop-level 报告或 benchmark 报告。不要一开始同时写论文、冲榜和重构全部代码。</p></div></section>
<section><h2>从本地实验到研究问题</h2><div class="grid">
<article class="card"><h3>R1 · Offline / closed-loop mismatch</h3><p>为什么 action MSE 或 rollout MSE 变好，闭环 success 仍可能不变？本地 tiny policy 已经给出一个可扩展现象。</p></article>
<article class="card"><h3>R2 · Action controllability</h3><p>同一初始状态、不同动作序列，world model 预测的未来是否真的分叉？可比较 latent/image/state divergence。</p></article>
<article class="card"><h3>R3 · VLA embodiment mismatch</h3><p>SmolVLA 的 6-D action chunk 与 PushT 的 2-D 平面动作不匹配；接口跑通不是 embodiment 迁移。</p></article>
<article class="card"><h3>R4 · World-model-assisted planning</h3><p>用 RSSM 想象候选动作的未来，再选择动作，最后在 gym-pusht 闭环验证。这是最贴近世界模型主线的方向。</p></article>
</div></section>
<section><h2>实践：建立机会雷达</h2><ol><li>打开 <a href="../reference/research-competition-portfolio.html">Research & Competition Portfolio</a>。</li><li>建立三列表：<b>入口</b>、<b>它测什么</b>、<b>我需要补什么证据</b>。</li><li>把 RoboWorld、AGIBOT World、RoboChallenge、GigaBrain、Embodied AI Workshop、WorldModelBench、WorldArena 各归入 challenge、benchmark 或观察项。</li><li>再查 CoRL / CVPR / ICRA / IROS / NeurIPS / ICLR workshop 页面，只记录仍在征稿或可等待下一届的入口。</li><li>为每个入口写一个停止条件：如果数据不可得、baseline 复现失败或算力超预算，就切到另一条产出线。</li></ol>
<div class="callout"><strong>日期纪律</strong><p>2026 年 10 月末时，许多 2026 会议 workshop 或 ICRA/CVPR 周期已经过了截稿。课程页面不猜日期；任何报名或提交前必须打开官方页面核对当届 deadline、资格和提交格式。</p></div></section>
<section><h2>实践：写一页 portfolio decision</h2><pre><code>portfolio/
├── decision.md         # 4 周内主线、6 周备选线、停止条件
├── challenge_track/    # 官方规则、baseline、提交日志
├── paper_track/        # 问题、实验表、图表、limitations
└── benchmark_track/    # 协议、复现命令、结果表

decision.md 必须回答：
1. 我的 claim 是什么？
2. 哪个官方/公开协议能检验它？
3. 至少 3 个 baseline 是什么？
4. 3 个 seed 是否可跑？
5. seen/unseen 如何划分？
6. offline 和 closed-loop 指标分别是什么？
7. latency / memory 是否报告？
8. 失败案例如何归档？</code></pre>
<div class="callout good"><strong>完成标准</strong><p>你能在 10 分钟内向队友说明：为什么选这个入口、第一周复现什么、第三周验证什么、哪个结果出现时立即切换路线。</p></div></section>
<section><h2>最低实验标准</h2><ul><li><b>Baseline：</b>random / previous action / tiny policy / stronger published baseline，至少三者可比。</li><li><b>Seeds：</b>核心表格至少 3 个 seed，报告 mean ± std 或完整分布。</li><li><b>Split：</b>episode-safe，明确 seen 与 unseen。</li><li><b>Metrics：</b>offline 与 closed-loop 分开，不混写一个“性能”。</li><li><b>Ablation：</b>移除核心组件，证明改进不是随机波动。</li><li><b>Cost：</b>记录 GPU、训练时长、推理 latency 和显存。</li><li><b>Failure：</b>保留最差案例和失败分类，不只展示成功案例。</li><li><b>Reproduction：</b>固定配置、seed、命令、环境版本和数据校验。</li></ul></section>
<section><h2>论文线不是“必须惊天结果”</h2><p>Workshop paper / technical report 可以承载更小的贡献：一个证据层级分析、一个 action controllability 度量、一个跨 embodiment 接口审计、或一个负结果复现报告。关键不是把名词堆高，而是把问题、协议、对照和边界写清楚。</p>
<pre><code>Paper skeleton:
1. One-sentence claim
2. Evidence gap in current evaluation
3. Protocol and baselines
4. Main result with uncertainty
5. Ablation
6. Failure taxonomy
7. Compute / latency cost
8. Limitations and next experiment</code></pre></section>
<section><h2>证据边界</h2><ul><li>RoboWorld 是默认 challenge 路线，不代表其他活动价值更低。</li><li>外部活动入口会变化；本课列的是发现渠道和检查方法，不是报名状态的实时数据库。</li><li>PushT、tiny RSSM、SmolVLA 的本地结果只能证明当前实验，不可外推为 SOTA 或跨任务成功。</li><li>没有 baseline、seed、split、失败分析的表格，不足以支撑论文 claim。</li><li>错过某个 2026 deadline 时，可以把成果转为 reproduction report、开源项目或下一届投稿。</li></ul></section>
""",
"source":"入口与检查方法见 <a href='https://roboworld2026.github.io' target='_blank'>RoboWorld</a>、<a href='https://embodied-ai.org' target='_blank'>Embodied AI Workshop</a>、<a href='https://www.corl.org/program/workshops' target='_blank'>CoRL workshops</a>、<a href='https://openreview.net' target='_blank'>OpenReview</a>、<a href='https://www.codabench.org' target='_blank'>CodaBench</a>；课程内汇总见 Research & Competition Portfolio。",
"quiz":{"q":"哪种结果最能支撑一个研究或参赛产出？","opts":[("可复现实验 + 多 baseline + 官方指标或清晰协议 + 失败分析","true"),("单个最好分数截图","false"),("只有模型参数文件","false"),("只有一段生成的视频","false")],"answer":0,"exp":"研究产出依赖证据链：协议、对照、重复性、指标边界和失败分析比单次高分更重要。"},
"artifacts":[("Research portfolio","../reference/research-competition-portfolio.html"),("Benchmark map","../reference/benchmark-map.html"),("Evaluation system","../reference/evaluation-system.html"),("RoboWorld 2026","../reference/roboworld-2026.html")],
},
]

def render_lesson(lesson, prev, nxt):
    opts = []
    correct = int(lesson["quiz"]["answer"])
    for i, (text, flag) in enumerate(lesson["quiz"]["opts"]):
        is_correct = "true" if i == correct else "false"
        opts.append(f'<button class="option" data-correct="{is_correct}" type="button"><span>{chr(65+i)}</span><span>{html.escape(text)}</span></button>')
    artifacts = "".join(f'<a class="badge" href="{href}">{html.escape(name)}</a> ' for name,href in lesson.get("artifacts",[]))
    prev_link = f'<div><span class="meta">上一课</span><br><a href="{prev["num"]}-{prev["slug"]}.html">{html.escape(prev["title"])}</a></div>' if prev else '<div></div>'
    nxt_link = f'<div style="text-align:right"><span class="meta">下一课</span><br><a href="{nxt["num"]}-{nxt["slug"]}.html">{html.escape(nxt["title"])}</a></div>' if nxt else '<div style="text-align:right"><span class="meta">继续</span><br><a href="index.html">回到课程目录</a></div>'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(lesson['title'])}</title><link rel="stylesheet" href="../assets/course.css"></head>
<body><div class="course-topbar"><div class="container compact"><a href="index.html">课程总目录</a><span>Lesson {html.escape(lesson['num'])} · {html.escape(lesson['module'])}</span></div></div>
<div class="progress-wrap"><div class="container" style="padding:0"><div class="progress-bar"><span></span></div><div class="meta" style="margin-top:6px">学习进度 <strong class="progress-percent">0%</strong></div></div></div>
<main class="container track">
<header class="hero"><span class="eyebrow">{html.escape(lesson['module'])}</span><h1>{html.escape(lesson['title'])}</h1><p class="meta">{html.escape(lesson['minutes'])} · 目标：{html.escape(lesson['goal'])}</p><p>{artifacts}</p>
<ul class="checklist"><li><label><input type="checkbox"><span>我能复述本课核心概念</span></label></li><li><label><input type="checkbox"><span>我完成了实践任务</span></label></li><li><label><input type="checkbox"><span>我通过了检索练习</span></label></li></ul></header>
{lesson['body']}
<section><h2>检索练习</h2><div class="quiz"><h3>{html.escape(lesson['quiz']['q'])}</h3><div class="options">{''.join(opts)}</div><div class="feedback">选择一个答案</div><div class="explanation">{lesson['quiz']['exp']}</div></div></section>
<section><h2>本课一手来源</h2><p>{lesson['source']}</p><div class="callout blue"><strong>有疑问就问</strong><p>把不理解的地方直接发给老师/agent，最好附上你观察到的现象和报错。</p></div></section>
<nav class="lesson-nav">{prev_link}{nxt_link}</nav><div class="source-note">Course file: lessons/{lesson['num']}-{lesson['slug']}.html</div></main><script src="../assets/course.js"></script></body></html>'''

def render_index(lessons):
    cards=[]
    for l in lessons:
        artifacts = "".join(f'<a class="badge" href="{href}">{name}</a> ' for name,href in l.get("artifacts",[]))
        cards.append(f'''<article class="card track"><h3><a href="{l['num']}-{l['slug']}.html">{l['num']} · {html.escape(l['title'])}</a></h3><p class="meta">{html.escape(l['module'])} · {html.escape(l['minutes'])}</p><p>{html.escape(l['goal'])}</p><p>{artifacts}</p><label><input type="checkbox"><span>已完成</span></label></article>''')
    refs = ''.join(f'<article class="card"><h3><a href="../reference/{p}">{t}</a></h3><p>{d}</p></article>' for p,t,d in [
        ('basic-introduction.html','基本介绍','概念边界、闭环流程、三条路线'),
        ('evaluation-system.html','评价体系','interface / offline / closed-loop 与指标陷阱'),
        ('benchmark-map.html','比赛与 Benchmark 地图','导航、操作、世界模型、真机平台'),
        ('roboworld-2026.html','RoboWorld 2026 产出','WorldNav 主目标、里程碑、提交包'),
        ('research-competition-portfolio.html','Research & Competition Portfolio','比赛、论文、benchmark 三条产出线'),
        ('field-map.html','World Model 全景图','五个层次和证据等级'),
        ('pusht-lab.html','PushT 数据手册','schema、统计和实践命令'),
        ('rssm-notebook.html','RSSM 速查本','posterior/prior/GRU/decoder'),
        ('vla-notebook.html','VLA 速查本','action chunk、flow matching、embodiment'),
        ('frontier-map.html','研究前沿地图','Cosmos、Dreamer、Genie、V-JEPA、VLA'),
    ])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>World Models & Embodied AI Course</title><link rel="stylesheet" href="../assets/course.css"></head>
<body><div class="course-topbar"><div class="container compact"><a href="#learning-route">课程总目录</a><span>14 lessons · 10 references</span></div></div>
<div class="progress-wrap"><div class="container" style="padding:0"><div class="progress-bar"><span></span></div><div class="meta" style="margin-top:6px">课程进度 <strong class="progress-percent">0%</strong></div></div></div>
<main class="container track"><header class="hero"><span class="eyebrow">Course</span><h1>World Models & Embodied AI</h1><p class="meta">14 lessons · knowledge + practice · Cosmos / Dreamer / PushT / SmolVLA · research portfolio</p>
<ul class="checklist"><li><label><input type="checkbox"><span>我已经读过 MISSION.md</span></label></li><li><label><input type="checkbox"><span>我已经准备好远端实验环境</span></label></li><li><label><input type="checkbox"><span>我知道课程进度会保存在本浏览器</span></label></li></ul></header>
<section id="learning-route"><h2>目录总览</h2><table><thead><tr><th>模块</th><th>课程</th><th>学完后能做什么</th><th>推荐入口</th></tr></thead><tbody>
<tr><td>A · Orientation</td><td><a href="0001-mental-map.html">0001</a></td><td>分清 world model、policy、VLA、benchmark、challenge。</td><td><a class="badge" href="../reference/basic-introduction.html">基本介绍</a> <a class="badge" href="../reference/field-map.html">全景图</a></td></tr>
<tr><td>B · Data</td><td><a href="0002-pusht-dataset.html">0002</a> · <a href="0003-baseline-leakage.html">0003</a></td><td>读机器人数据集 schema，设计不泄漏的 baseline。</td><td><a class="badge" href="../reference/pusht-lab.html">PushT 手册</a></td></tr>
<tr><td>C · Video world models</td><td><a href="0004-cosmos-video.html">0004</a> · <a href="0005-video-latent.html">0005</a></td><td>理解 Cosmos 视频生成和 latent 组件。</td><td><a class="badge" href="../reference/frontier-map.html">前沿地图</a></td></tr>
<tr><td>D · Latent world models</td><td><a href="0006-rssm-training.html">0006</a> · <a href="0007-open-loop-rollout.html">0007</a></td><td>训练 RSSM，诊断 rollout 误差累积。</td><td><a class="badge" href="../reference/rssm-notebook.html">RSSM 速查本</a></td></tr>
<tr><td>E · Policies</td><td><a href="0008-imitation-policy.html">0008</a> · <a href="0009-closed-loop.html">0009</a></td><td>训练 imitation policy，解释闭环指标。</td><td><a class="badge" href="../reference/evaluation-system.html">评价体系</a></td></tr>
<tr><td>F · VLA</td><td><a href="0010-smolvla-interface.html">0010</a> · <a href="0011-embodiment-mismatch.html">0011</a></td><td>检查 VLA 接口，识别 embodiment mismatch。</td><td><a class="badge" href="../reference/vla-notebook.html">VLA 速查本</a></td></tr>
<tr><td>G · Integration</td><td><a href="0012-capstone.html">0012</a></td><td>写出可复现、可证伪的 capstone 设计。</td><td><a class="badge" href="../reference/benchmark-map.html">Benchmark 地图</a></td></tr>
<tr><td>H · Challenge Output</td><td><a href="0013-roboworld-output.html">0013</a></td><td>把课程成果整理为 RoboWorld WorldNav 项目包和提交计划。</td><td><a class="badge" href="../reference/roboworld-2026.html">RoboWorld 2026</a></td></tr>
<tr><td>I · Research Portfolio</td><td><a href="0014-research-portfolio.html">0014</a></td><td>把同一套能力扩展到比赛、论文和 benchmark 三条产出线。</td><td><a class="badge" href="../reference/research-competition-portfolio.html">Portfolio 地图</a></td></tr>
</tbody></table></section>
<section><h2>学习路线</h2><div class="grid">{''.join(cards)}</div></section>
<section><h2>参考手册</h2><div class="grid">{refs}</div></section>
<section><h2>怎么学最有效</h2><div class="grid"><article class="card"><h3>1. 先回忆</h3><p>每课先看标题，尝试凭记忆写下三个关键词。</p></article><article class="card"><h3>2. 再实践</h3><p>跑命令或看本地 artifact，不要只读文字。</p></article><article class="card"><h3>3. 后检索</h3><p>完成 quiz，错题要回参考手册。</p></article><article class="card"><h3>4. 做判断</h3><p>每课最后问：这个结果能证明什么，不能证明什么？</p></article></div></section>
<div class="source-note">课程文件位于 /Users/peppa/code/worldmodel；实验素材来自本地与 h200_1727。</div></main><script src="../assets/course.js"></script></body></html>'''

for i,l in enumerate(lessons):
    prev = lessons[i-1] if i>0 else None
    nxt = lessons[i+1] if i<len(lessons)-1 else None
    (LESSONS/f"{l['num']}-{l['slug']}.html").write_text(render_lesson(l,prev,nxt), encoding='utf-8')
(LESSONS/"index.html").write_text(render_index(lessons), encoding='utf-8')
print(f"generated {len(lessons)} lessons + index")
