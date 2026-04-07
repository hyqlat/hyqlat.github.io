---
permalink: /
title: ""
excerpt: ""
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---
{% if site.google_scholar_stats_use_cdn %}
{% assign gsDataBaseUrl = "https://cdn.jsdelivr.net/gh/" | append: site.repository | append: "@" %}
{% else %}
{% assign gsDataBaseUrl = "https://raw.githubusercontent.com/" | append: site.repository | append: "/" %}
{% endif %}
{% assign url = gsDataBaseUrl | append: "google-scholar-stats/gs_data_shieldsio.json" %}

<span class='anchor' id='about-me'></span>

<!-- I am a master's student in the School of Computer Science at Sun Yat-sen University. I graduated from the Department of Computer Science and Technology at Sun Yat-sen University with a bachelor's degree.  -->
I completed both my Bachelor's and Master's studies at Sun Yat-sen University, where I was advised by Prof. <a href="https://isee-ai.cn/~hujianfang/">Jian-Fang Hu</a>. At present, four of my papers have been published. <a href='https://scholar.google.com/citations?user=r533xwkAAAAJ'><img src="https://img.shields.io/endpoint?url={{ url | url_encode }}&logo=Google%20Scholar&labelColor=f6f6f6&color=9cf&style=flat&label=引用"></a>

Research area：

- 3D Human Motion Prediction
- Continual Learning

<span class='anchor' id='-xl'></span>

# 🎓 Educations

- *2022.09 - 2025.06*, <a href="https://www.sysu.edu.cn/"><img class="svg" src="images/SYSU_logo.svg" width="20pt"></a> Sun Yat-sen University, MS
- *2018.09 - 2022.06*, <a href="https://www.sysu.edu.cn/"><img class="svg" src="images/SYSU_logo.svg" width="20pt"></a> Sun Yat-sen University, BS

<span class='anchor' id='-lwzl'></span>

# 📝 Publications

---

<div class='paper-box'><div class='paper-box-image'><div><div class="badge">TPAMI</div><img src='images/tpami2026.png' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- **Tang, Jianwei** and Hu, Jian-Fang and Liang, Tianming and Lin, Xiaotong and Sun, Jiangxin and Zheng, Wei-Shi and Lai, Jianhuang. Human Motion Prediction via Continual Prior Compensation. *IEEE Transactions on Pattern Analysis and Machine Intelligence*. 2026, 48(5): 5131-5146. (TPAMI)
  [[Page]](https://ieeexplore.ieee.org/abstract/document/11342290)
   <!-- [[PDF]](https://ieeexplore.ieee.org/abstract/document/11342290) -->
   <!-- [[Code]](https://github.com/hyqlat/ATACB) -->
  

</div>
</div>

<div class='paper-box'><div class='paper-box-image'><div><div class="badge">CVPR 2025</div><img src='images/overview.jpg' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- **Jianwei Tang**, Hong Yang, Tengyue Chen, Jian-Fang Hu. Stochastic Human Motion Prediction with Memory of Action Transition and Action Characteristic. *IEEE Conference on Computer Vision and Pattern Recognition*, 2025, 1883-1893. (CVPR 2025)
  [[Homepage]](https://hyqlat.github.io/STABACB.github.io/) [[PDF]](https://openaccess.thecvf.com/content/CVPR2025/papers/Tang_Stochastic_Human_Motion_Prediction_with_Memory_of_Action_Transition_and_CVPR_2025_paper.pdf) [[Code]](https://github.com/hyqlat/ATACB)

</div>
</div>

<div class='paper-box'><div class='paper-box-image'><div><div class="badge">NeurIPS 2023</div><img src='images/XDSY.jpg' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- **Jianwei Tang**, Jiangxin Sun, Xiaotong Lin, Lifang Zhang, Wei-Shi Zheng, Jian-Fang Hu. Temporal Continual Learning with Prior Compensation for Human Motion Prediction. *Advances in Neural Information Processing Systems*, 2023, 36: 65837-65849. (NeurIPS 2023)
  [[Page]](https://proceedings.neurips.cc/paper_files/paper/2023/hash/cf7a83a5342befd11d3d65beba1be5b0-Abstract-Conference.html) [[PDF]](https://proceedings.neurips.cc/paper_files/paper/2023/file/cf7a83a5342befd11d3d65beba1be5b0-Paper-Conference.pdf) [[Code]](https://github.com/hyqlat/TCL)

</div>
</div>



<div class='paper-box'><div class='paper-box-image'><div><div class="badge">VI 2023</div><img src='images/kvlstm.jpg' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- **Jianwei Tang**, Jieming Wang, Jian-Fang Hu. Predicting human poses via recurrent attention network. *Visual Intelligence*. 2023, 1(1): 18.
  [[Page]](https://link.springer.com/article/10.1007/s44267-023-00020-z) [[PDF]](https://link.springer.com/content/pdf/10.1007/s44267-023-00020-z.pdf) 

</div>
</div>


<span class='anchor' id='-intern'></span>

# 💻 Internships

- *2024.05 - 2024.08*, **Tencent**, Machine Learning Engineer
- *2024.12 - 2025.01*, **Math Magic**, Machine Learning Engineer

<span class='anchor' id='-services'></span>

# 🤝 Services

Conference Reviewer

-  2025: NeurIPS

<span class='anchor' id='-proj'></span>

# 🔖 Projects


<div class='paper-box'><div class='paper-box-image'><div><div class="badge">3D Human Render</div><img src='images/pose1.jpg' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- A tool for 3D human motion visualization. Supports the SMPL model and skeleton point representation. The visualization results include lighting, ground, shadows, and allow for customizing rendering colors, etc. [[Code]](https://github.com/hyqlat/PyRender-for-Human-Mesh/tree/Mesh_and_Skeleton)

</div>
</div>

<div class='paper-box'><div class='paper-box-image'><div><div class="badge">Scene Editor</div><img src='images/sceneeditor.jpg' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- This project is a 3D scene editor developed using C++ and OpenGL, capable of loading skyboxes, heightmap terrains, and obj models. It originated from a group assignment in a computer graphics course at Sun Yat-sen University. [[Code]](https://github.com/bryanT4N/3DSE)

</div>
</div>

<div class='paper-box'><div class='paper-box-image'><div><div class="badge">Chinese Chess</div><img src='images/ChineseChess.png' alt="sym" width="100%"></div></div>
<div class='paper-box-text' markdown="1">

- Chinese Chess Game, developed by C++. [[Code]](https://github.com/hyqlat/Chinese-Chess)

</div>
</div>

<!-- <span class='anchor' id='-ryjx'>

# 🏅 荣誉奖项

- *2015.11* 获得 第十四届“挑战杯”全国大学生课外学术科技作品竞赛 `一等奖`
- *2015.06* 获得 第十三届“挑战杯”四川大学生课外学术科技作品竞赛 `一等奖` [[新闻]](https://www.sc.gov.cn/10462/10778/10876/2015/7/1/10341562.shtml)
- *2014.12* 获得 第四届全国大学生工程训练综合能力竞赛（四川赛区） `一等奖`

<span class='anchor' id='-xshy'></span>

# 🏛️ 学术会议

- *2021.10*, 全国电磁无损检测技术研讨会 暨 中国机械工程学会无损检测分会电磁专业技术大会第十一届第四次全体会议, 陕西西安, 受邀报告
- *2019.09*, 第十九届国际应用电磁学与力学会议 (ISEM 2019), 江苏南京, 海报
- *2017.10*, 第六届中国国际管道会议 (CIPC 2017), 河北廊坊

<span class='anchor' id='-gzsx'></span> -->

<!-- # 💻 工作实习

- *2018.05 - 2020.02*, 重庆长江轴承股份有限公司, 重庆
- *2020.11.25 - 2020.12.02*, 湖北新冶钢有限公司, 湖北黄石
- *2017.6 - 2021.1*, 制造装备数字化国家工程研究中心, 湖北武汉 -->
