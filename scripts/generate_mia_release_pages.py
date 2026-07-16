#!/usr/bin/env python3
"""Generate the three detailed ENOMOTO MIA release pages."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bellflower1209.github.io/suzuka-official-music"
CHANNEL = "https://www.youtube.com/@bellflower5215"

SONGS = [
    {
        "slug": "mia",
        "name": "M・I・A",
        "title": "M・I・A｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「M・I・A」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。好きになったらもう戻れない、榎本魅愛の存在感を刻むJ-POP。",
        "social_description": "好きになったら、もう戻れない。榎本魅愛という存在と、恋に落ちた高揚感を刻む「M・I・A」の公式ページ。",
        "image": "mv-mia.jpg",
        "youtube_id": "WzcXyuAI_FM",
        "upload_date": "2026-07-13",
        "video_title": "好きになったら、もう戻れない。榎本魅愛『M・I・A』Official Music Video",
        "video_description": "榎本魅愛というアーティスト自身の存在感と、一度好きになったら戻れない恋の高揚感を描く「M・I・A」の公式ミュージックビデオ。",
        "hero_title": "M・I・A",
        "hero_lead": "名前を呼ぶたび、恋は深くなる。<br/>好きになったら、もう戻れない。",
        "art_badge": "M・I・A ♡",
        "intro_title": "名前そのものが、<br/>恋のフックになる。",
        "intro": [
            "「M・I・A」は、榎本魅愛というアーティスト自身の存在感と、恋に落ちた瞬間の高揚感をまっすぐに打ち出すJ-POPです。",
            "一度好きになったら、気持ちはもう恋を知る前の場所には戻れない。短く印象的なタイトルが、何度も名前を呼びたくなるような強いフックとして響きます。",
            "ジャケットには「君を好きになったことで本当のわたしが見つかった」という言葉が添えられ、誰かを想うことで自分自身の輪郭まで鮮明になっていく世界観を伝えています。",
        ],
        "catchcopy": "「好きになったら、<br/>もう戻れない。」",
        "catch_label": "MIA: MY HEART IN LOVE",
        "story": [
            "このページで紹介する世界観は、公式動画タイトルとジャケットに記された言葉から読み取れる範囲をまとめたものです。中心にあるのは、恋をきっかけに本当の自分を見つけていく感覚です。",
            "アルファベットを区切った「M・I・A」という表記は、アーティスト名そのものを視覚的にも耳にも残るフレーズへ変えています。名前と恋心が重なる構成が、榎本魅愛の存在を強く印象づけます。",
            "柔らかなピンク、花びら、光に包まれたジャケットは、恋の甘さと高揚感を表現しています。強いタイトルと繊細なビジュアルの組み合わせが、この曲らしい余韻を作っています。",
        ],
        "keywords": ["M・I・A", "恋の高揚感", "本当のわたし", "名前", "J-POP"],
        "video_heading": "名前と恋が重なる、<br/>榎本魅愛のシグネチャーソング。",
        "related": ["hyakumankoku", "muteki", "toriatsukai", "sukitte"],
        "theme": "--mia-pink:#f44f96;--mia-hot-pink:#ff5ca8;--mia-violet:#b77aff;",
    },
    {
        "slug": "hyakumankoku",
        "name": "百万告",
        "title": "百万告｜榎本魅愛 デビュー曲・公式MV｜SUZUKA",
        "description": "榎本魅愛「百万告」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。『好き』は一回じゃ足りない、まっすぐな恋心を描いたJ-POP。",
        "social_description": "「好き」は、一回じゃ足りない。まっすぐで大胆な恋心を届ける、榎本魅愛のデビュー曲「百万告」。",
        "image": "mv-hyakumankoku.jpg",
        "youtube_id": "QteunhFn9Dk",
        "upload_date": "2026-07-12",
        "video_title": "【デビュー曲】「好き」は一回じゃ足りない。榎本魅愛『百万告』Official Music Video",
        "video_description": "「好き」という気持ちは一度伝えるだけでは足りないという、まっすぐで大胆な恋心を描く榎本魅愛のデビュー曲「百万告」の公式ミュージックビデオ。",
        "hero_title": "百万告",
        "hero_lead": "何回だって、好きは更新される。<br/>一回じゃ足りない想いを、君へ。",
        "art_badge": "DEBUT SONG ♡",
        "intro_title": "「好き」を、<br/>何度でも届ける。",
        "intro": [
            "「百万告」は、「好き」という気持ちは一度伝えるだけでは足りないという、まっすぐで大胆な恋心を描いた榎本魅愛のデビュー曲です。",
            "一度の告白で終わるのではなく、今日も明日も、気持ちが増えるたびに何度でも伝えたい。タイトルは、そんな終わらない告白を「百万告」という印象的な言葉で表しています。",
            "明るいピンクのステージと、手を差し伸べる榎本魅愛のジャケットが、想いを相手へ届けようとする楽曲のまっすぐさを視覚でも伝えています。",
        ],
        "catchcopy": "「『好き』は、<br/>一回じゃ足りない。」",
        "catch_label": "ONE LOVE, A MILLION TIMES",
        "story": [
            "公式動画ではデビュー曲として公開され、ジャケットにも「百万回でも『好き』って言うよ」「何回だって更新中」といった言葉が配置されています。そこから伝わるのは、ためらいよりも気持ちを届けることを選ぶ恋の姿です。",
            "「告白」の一文字を置き換えた「百万告」というタイトルは、大きな数字と短い言葉を組み合わせ、想いの強さと回数の多さを一度に印象づけます。",
            "マイク、バンドセット、きらめくハートに囲まれたビジュアルは、恋心をステージからまっすぐ届けるデビュー曲らしい華やかさを持っています。",
        ],
        "keywords": ["デビュー曲", "好き", "告白", "何度でも", "J-POP"],
        "video_heading": "終わらない告白から始まる、<br/>榎本魅愛のデビュー曲。",
        "related": ["mia", "muteki", "toriatsukai", "sukitte"],
        "theme": "--mia-pink:#ff6e9f;--mia-hot-pink:#ff337f;--mia-violet:#ff9ac2;",
        "position": "デビュー曲",
    },
    {
        "slug": "muteki-jikan-ato-3byou",
        "name": "無敵時間、あと3秒",
        "title": "無敵時間、あと3秒｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「無敵時間、あと3秒」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。恋の一歩を踏み出す直前の勇気を描いたJ-POP。",
        "social_description": "無敵になれるのは、あと3秒。ゲーム感覚と恋の緊張感を重ねた、榎本魅愛「無敵時間、あと3秒」。",
        "image": "mv-muteki.jpg",
        "youtube_id": "DPnFtRFnH5c",
        "upload_date": "2026-07-13",
        "video_title": "無敵になれるのは、あと3秒。榎本魅愛『無敵時間、あと3秒』Official Music Video",
        "video_description": "好きな人の前で一歩踏み出す直前の短く強い勇気を、ゲーム感覚と恋愛の緊張感で描く「無敵時間、あと3秒」の公式ミュージックビデオ。",
        "hero_title": "無敵時間、<br/><em>あと3秒</em>",
        "hero_lead": "勇気のゲージが切れる、その前に。<br/>恋の一歩を、3・2・1で踏み出す。",
        "art_badge": "3 · 2 · 1 · GO ♡",
        "intro_title": "勇気が消える前に、<br/>一歩だけ前へ。",
        "intro": [
            "「無敵時間、あと3秒」は、好きな人の前で一歩踏み出す直前の、短く強い勇気を描いた榎本魅愛のJ-POPです。",
            "ずっと無敵でいられるわけではない。だからこそ、勇気の残り時間がゼロになる前に動き出す。恋の緊張感を、ゲームのカウントダウンに重ねています。",
            "HPゲージ、ハート、LEVEL UP、3・2・1 GO。ジャケットに並ぶゲーム画面のような要素が、告白前の焦りと勢いをポップに可視化しています。",
        ],
        "catchcopy": "「無敵になれるのは、<br/>あと3秒。」",
        "catch_label": "READY? 3 · 2 · 1 · GO",
        "story": [
            "タイトルと公式動画が示すのは、勇気には限りがあるという感覚です。好きな人へ近づく直前だけ、自分が少し無敵になれたように感じる。その短い時間を「あと3秒」というカウントダウンで表しています。",
            "恋愛の緊張感をHPゲージや残り時間へ置き換えることで、迷いと決断の瞬間がゲームのミッションのように分かりやすく伝わります。",
            "ネオンカラーと疾走感のあるジャケット、前へ手を伸ばすポーズは、立ち止まるより先に踏み出す勢いを強調しています。既存サイトとジャケットでは5th Singleとして紹介されています。",
        ],
        "keywords": ["3秒", "勇気", "カウントダウン", "ゲーム", "J-POP"],
        "video_heading": "3・2・1で踏み出す、<br/>恋のカウントダウン。",
        "related": ["mia", "hyakumankoku", "toriatsukai", "sukitte"],
        "theme": "--mia-pink:#ff4fa3;--mia-hot-pink:#ff297f;--mia-violet:#5d86ff;",
        "position": "5th Single",
    },
    {
        "slug": "tokenai-mahou-wo-ai-to-yobu",
        "name": "解けない魔法を、愛と呼ぶ",
        "title": "解けない魔法を、愛と呼ぶ｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「解けない魔法を、愛と呼ぶ」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。恋によって変わった心を、解けない魔法として描くJ-POP。",
        "social_description": "恋によって変わった心を、解けない魔法として描く榎本魅愛のロマンティックなJ-POP。",
        "image": "mv-mahou.jpg",
        "youtube_id": "CAFQ-d7YHPQ",
        "upload_date": "2026-07-13",
        "video_title": "恋の魔法が解けたあと、それでも君を選べますか。榎本魅愛『解けない魔法を、愛と呼ぶ』Official Music Video",
        "video_description": "恋によって変わった心と、魔法が解けたあとにも残る想いを描く「解けない魔法を、愛と呼ぶ」の公式ミュージックビデオ。",
        "hero_title": "解けない魔法を、<br/><em>愛と呼ぶ</em>",
        "hero_lead": "魔法が解けても、残るものがある。<br/>変わってしまった心を、愛と呼ぶ。",
        "art_badge": "6TH SINGLE · MAGIC ♡",
        "intro_title": "解けないからこそ、<br/>愛と呼べるもの。",
        "intro": [
            "「解けない魔法を、愛と呼ぶ」は、恋によって変わってしまった心を、解けない魔法になぞらえて描くロマンティックなJ-POPです。",
            "恋の始まりは魔法のように眩しくても、時間がたてば景色は変わっていく。それでも残り続ける気持ちを、この楽曲は「愛」という言葉へつなげています。",
            "夕暮れの光、花、きらめく軌跡に包まれたジャケットが、現実と幻想の境界にいるような柔らかな世界観を伝えています。",
        ],
        "catchcopy": "「解けないからこそ、<br/>それを愛と呼ぶ。」",
        "catch_label": "A SPELL THAT STAYS",
        "story": [
            "公式動画タイトルは、恋の魔法が解けたあとにも相手を選べるかを問いかけています。この楽曲では、瞬間的なときめきだけではなく、変化のあとに残る感情が描かれていると受け取れます。",
            "ジャケットには、魔法が解けないならそれは愛かもしれない、という世界観を補う言葉が配置されています。タイトルとビジュアルが重なり、恋から愛へ移っていく心の時間を印象づけます。",
            "淡い紫とピンク、光の線が作る幻想的な画面は、形のない感情を魔法として見せるロマンティックな印象を与えます。ジャケットでは6th Singleと確認できます。",
        ],
        "keywords": ["魔法", "愛", "変わる心", "余韻", "J-POP"],
        "video_heading": "魔法が解けたあとに残る、<br/>愛という答え。",
        "related": ["mia", "hanabi", "sukitte", "mermaid"],
        "theme": "--mia-pink:#ee8fbd;--mia-hot-pink:#d36aa6;--mia-violet:#a988ff;",
        "position": "6th Single",
    },
    {
        "slug": "kimi-to-nara-last-boss-made",
        "name": "君とならラスボスまで",
        "title": "君とならラスボスまで｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「君とならラスボスまで」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。恋と冒険を重ねた、前向きなRPGラブソング。",
        "social_description": "どんな困難も君となら越えていける。恋と冒険を重ねた、榎本魅愛の前向きなRPGラブソング。",
        "image": "mv-lastboss.jpg",
        "youtube_id": "YVNs3I-KaHI",
        "upload_date": "2026-07-13",
        "video_title": "人生に攻略本はない。でも君とならラスボスまで。榎本魅愛『君とならラスボスまで』Official Music Video",
        "video_description": "恋愛とRPGの冒険を重ね、どんな困難も好きな人となら越えていける気持ちを描く「君とならラスボスまで」の公式ミュージックビデオ。",
        "hero_title": "君となら<br/><em>ラスボスまで</em>",
        "hero_lead": "人生に攻略本はない。<br/>それでも君となら、最後まで行ける。",
        "art_badge": "4TH SINGLE · QUEST ♡",
        "intro_title": "恋と冒険を、<br/>ふたりで攻略する。",
        "intro": [
            "「君とならラスボスまで」は、恋愛とRPGの世界観を重ね、どんな困難も好きな人となら越えられるという気持ちを描く前向きなラブソングです。",
            "人生には決められた攻略本も、正解のルートもない。それでも隣に信じられる相手がいれば、最後の敵まで進んでいける。そんな心強さを冒険の言葉で表しています。",
            "城、地図、コンパス、クエスト画面を思わせるジャケットが、ふたりの未来をひとつの壮大な冒険として見せています。",
        ],
        "catchcopy": "「君となら、<br/>最後の敵まで怖くない。」",
        "catch_label": "LET'S GO ON AN ADVENTURE",
        "story": [
            "公式動画タイトルの「人生に攻略本はない」という言葉は、恋にも未来にも決められた正解がないことを示しています。そのうえで、君とならラスボスまで進めるという信頼が楽曲の軸になっています。",
            "RPGのラスボスは、物語の最後に待つ最大の試練です。その言葉を恋愛に重ねることで、楽しい場面だけでなく困難な局面も一緒に越えたいという気持ちが伝わります。",
            "ジャケットのメニュー画面、マップ、クエスト表示は、恋の未来を選択と冒険の連続として見せます。ジャケットでは4th Singleと確認できます。",
        ],
        "keywords": ["RPG", "冒険", "ラスボス", "ふたり", "J-POP"],
        "video_heading": "攻略本のない未来を、<br/>君と進むRPGラブソング。",
        "related": ["muteki", "ai", "mia", "mermaid"],
        "theme": "--mia-pink:#ef79c7;--mia-hot-pink:#d850d8;--mia-violet:#6f7dff;",
        "position": "4th Single",
    },
    {
        "slug": "ai-demo-wakaranai",
        "name": "AIでもわからない",
        "title": "AIでもわからない｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「AIでもわからない」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。計算では答えの出ない恋心を描いたAIラブソング。",
        "social_description": "どれだけ分析しても、この恋だけは計算できない。榎本魅愛が歌うAIラブソング。",
        "image": "mv-ai.jpg",
        "youtube_id": "5jmTo3Jb5sI",
        "upload_date": "2026-07-13",
        "video_title": "AIなら何でもわかる。でも、君の気持ちだけわからない。榎本魅愛『AIでもわからない』Official Music Video",
        "video_description": "どれだけ分析しても計算では答えが出ない恋心を、AIと人間の感情を重ねて描く「AIでもわからない」の公式ミュージックビデオ。",
        "hero_title": "AIでも<br/><em>わからない</em>",
        "hero_lead": "分析できても、答えは出ない。<br/>君の気持ちだけが、まだ読めない。",
        "art_badge": "3RD SINGLE · THINKING ♡",
        "intro_title": "この恋だけは、<br/>計算できない。",
        "intro": [
            "「AIでもわからない」は、どれだけ分析しても計算できない恋心を、AIと人間の感情を重ねて描くラブソングです。",
            "知識やデータが増えても、好きな人の本当の気持ちだけは読み切れない。答えを急ぐほど迷ってしまう、恋の不確かさをデジタルな言葉で表しています。",
            "スマートフォン、既読表示、メッセージ画面、Thinkingという表示を配したジャケットが、送信ボタンを押す前の迷いを可視化しています。",
        ],
        "catchcopy": "「この恋だけは、<br/>計算できない。」",
        "catch_label": "LOVE HAS NO ALGORITHM",
        "story": [
            "公式動画タイトルは、AIなら多くのことを理解できても、相手の気持ちだけはわからないという対比を示しています。この楽曲では、情報では解決できない恋の揺れが描かれています。",
            "ジャケットにある既読表示や「好きって送っていいのかな」という問いは、相手の反応を予測できないメッセージ送信前の緊張を印象づけます。",
            "デジタルなUIと柔らかなピンクの光を組み合わせることで、機械的な分析と人間らしいためらいが同じ画面に共存しています。ジャケットでは3rd Singleと確認できます。",
        ],
        "keywords": ["AI", "計算", "既読", "メッセージ", "J-POP"],
        "video_heading": "データでは解けない、<br/>君の気持ちという難問。",
        "related": ["muteki", "lastboss", "mia", "toriatsukai"],
        "theme": "--mia-pink:#f28fc4;--mia-hot-pink:#ec55b4;--mia-violet:#55a8ff;",
        "position": "3rd Single",
    },
    {
        "slug": "kimi-wa-hanabi",
        "name": "君は花火",
        "title": "君は花火｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「君は花火」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。夏の夜と一瞬の恋の輝きを描いたJ-POP。",
        "social_description": "夏の夜空を染める花火のように、強く眩しい恋の記憶を描く榎本魅愛のサマーラブソング。",
        "image": "mv-hanabi.jpg",
        "youtube_id": "ohylad3AWYI",
        "upload_date": "2026-07-12",
        "video_title": "夏が来るたび、君を思い出す。榎本魅愛『君は花火』Official Music Video",
        "video_description": "一瞬で夜空を染める花火のように、強く眩しい恋の記憶を描く「君は花火」の公式ミュージックビデオ。",
        "hero_title": "君は<br/><em>花火</em>",
        "hero_lead": "夏が来るたび、光がよみがえる。<br/>消えても残る、あの日の恋。",
        "art_badge": "SUMMER NIGHT ♡",
        "intro_title": "消えたあとにも、<br/>光は残っている。",
        "intro": [
            "「君は花火」は、一瞬で夜空を染める花火のように、強く眩しい恋の記憶を描く夏のラブソングです。",
            "同じ季節が巡るたび、過ぎ去った時間と好きだった人の姿が鮮やかによみがえる。短い輝きだからこそ忘れられない、夏の恋の余韻を伝えています。",
            "浴衣姿で花火を見上げるジャケットが、夏の夜に残された想いと、その記憶を歌へ託す静かな時間を映しています。",
        ],
        "catchcopy": "「消えても、<br/>光だけは残ってる。」",
        "catch_label": "THE LIGHT STAYS",
        "story": [
            "公式動画タイトルの「夏が来るたび、君を思い出す」という言葉からは、季節と記憶が結びついた楽曲の世界が読み取れます。",
            "花火は長くは続かなくても、その瞬間の光は強く記憶に残ります。この楽曲では、終わったあとも消えない恋の感情が、夜空の花火に重ねられています。",
            "暗い夜空と暖かな花火、静かにマイクを持つ姿の対比が、華やかな思い出と切ない余韻を同時に感じさせます。",
        ],
        "keywords": ["夏", "花火", "記憶", "ひと夏", "J-POP"],
        "video_heading": "夏が巡るたびによみがえる、<br/>一瞬の恋の光。",
        "related": ["sukitte", "mahou", "mia", "mermaid"],
        "theme": "--mia-pink:#f178a6;--mia-hot-pink:#e94788;--mia-violet:#f19a62;",
    },
    {
        "slug": "sukitte-baretemo-ii",
        "name": "好きってバレてもいい",
        "title": "好きってバレてもいい｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「好きってバレてもいい」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。隠していた恋心を伝える勇気を描いたJ-POP。",
        "social_description": "隠していた恋心を、もう隠さなくてもいいと決める瞬間を描く榎本魅愛の可愛い恋愛ソング。",
        "image": "mv-sukitte-baretemo-ii.jpg",
        "width": 886,
        "height": 886,
        "youtube_id": "XP8yXMKFHVI",
        "upload_date": "2026-07-12",
        "video_title": "好きなの、たぶんもうバレてる。榎本魅愛『好きってバレてもいい』Official Music Video",
        "video_description": "隠していた恋心を、もう隠さなくてもいいと決める瞬間を描く「好きってバレてもいい」の公式ミュージックビデオ。",
        "hero_title": "好きって<br/><em>バレてもいい</em>",
        "hero_lead": "隠していた気持ちを、もう隠さない。<br/>好きなのは、たぶんもう伝わってる。",
        "art_badge": "HONEST LOVE ♡",
        "intro_title": "隠す恋から、<br/>伝える恋へ。",
        "intro": [
            "「好きってバレてもいい」は、隠していた恋心を、もう隠さなくてもいいと決める瞬間を描く、まっすぐで可愛い恋愛ソングです。",
            "気づかれないようにしてきた仕草も視線も、たぶん相手にはもう伝わっている。それなら逃げるのではなく、自分の気持ちを受け止めて前へ進もうとする勇気を描いています。",
            "夕方の街を背景にした柔らかなピンクのジャケットが、告白前の照れと、決心したあとの明るさを同時に感じさせます。",
        ],
        "catchcopy": "「もう、<br/>好きってバレてもいい。」",
        "catch_label": "NO MORE HIDING",
        "story": [
            "公式動画タイトルは「好きなの、たぶんもうバレてる」と語りかけます。知られたくない気持ちから、知られてもいい気持ちへ変わる境目が、この楽曲の中心にあります。",
            "タイトルには、告白するという強い宣言より少し手前の、可愛らしい覚悟があります。相手に気づかれることを受け入れた瞬間、恋が静かに前進する印象を与えます。",
            "自然な表情と夕暮れの光を生かしたジャケットは、大きな演出よりも日常の中で育った恋心を近くに感じさせます。",
        ],
        "keywords": ["好き", "勇気", "告白前", "本音", "J-POP"],
        "video_heading": "隠しきれない想いを、<br/>前へ進む勇気に変える。",
        "related": ["hyakumankoku", "mia", "hanabi", "toriatsukai"],
        "theme": "--mia-pink:#ff75ad;--mia-hot-pink:#ff4c99;--mia-violet:#f3a2ce;",
    },
    {
        "slug": "mermaid-merman",
        "name": "MERMAID×MERMAN",
        "title": "MERMAID×MERMAN｜榎本魅愛 公式MV・楽曲情報｜SUZUKA",
        "description": "榎本魅愛「MERMAID×MERMAN」の公式楽曲ページ。楽曲情報、制作ストーリー、MV、関連曲を紹介します。異なる世界に生きる2人の恋を描いた幻想的なJ-POP。",
        "social_description": "出会うはずのない異なる世界のふたりが恋をする、榎本魅愛の幻想的なラブソング。",
        "image": "mv-mermaid-merman.jpg",
        "width": 886,
        "height": 886,
        "youtube_id": "29fpeNtUqfY",
        "upload_date": "2026-07-12",
        "video_title": "出会うはずのない二人が、恋をした。榎本魅愛『MERMAID×MERMAN』Official Music Video",
        "video_description": "異なる世界に生きるふたりの出会いと恋を、海と人魚の幻想的なモチーフで描く「MERMAID×MERMAN」の公式ミュージックビデオ。",
        "hero_title": "MERMAID<br/><em>× MERMAN</em>",
        "hero_lead": "出会うはずのないふたりが、恋をした。<br/>違う世界の境界を、想いが越えていく。",
        "art_badge": "OCEAN ROMANCE ♡",
        "intro_title": "違う世界から、<br/>同じ海へ。",
        "intro": [
            "「MERMAID×MERMAN」は、異なる世界に生きるふたりの恋をモチーフにした、幻想的でロマンティックなJ-POPです。",
            "本来なら交わらないはずの場所にいたふたりが出会い、境界を越えて惹かれ合う。海の広さと深さが、距離を超えてつながる想いを印象づけます。",
            "夕暮れの海、波、きらめく装飾に包まれたふたりのジャケットが、現実から離れた物語の一場面のような世界を作っています。",
        ],
        "catchcopy": "「違う世界でも、<br/>恋は同じ海へ辿り着く。」",
        "catch_label": "TWO WORLDS, ONE OCEAN",
        "story": [
            "公式動画タイトルの「出会うはずのない二人が、恋をした」という言葉が、この物語の出発点です。この楽曲では、違いそのものが恋を遠ざけるのではなく、ふたりを引き寄せる物語として描かれています。",
            "MERMAIDとMERMANを掛け合わせたタイトルは、ふたつの存在が並び、ひとつの物語になることを視覚的にも示しています。",
            "海面の上と下、夕暮れと水中の青を一枚に収めたジャケットは、ふたつの世界が接する瞬間を幻想的に見せています。",
        ],
        "keywords": ["人魚", "海", "異なる世界", "出会い", "J-POP"],
        "video_heading": "境界を越えて出会う、<br/>幻想的なオーシャンラブストーリー。",
        "related": ["mahou", "hanabi", "lastboss", "mia"],
        "theme": "--mia-pink:#d594c7;--mia-hot-pink:#aa65b5;--mia-violet:#3e8fc9;",
    },
]

RELATED = {
    "mia": ("M・I・A", "mv-mia.jpg", "../mia/", "OFFICIAL MV", 1280, 720),
    "hyakumankoku": ("百万告", "mv-hyakumankoku.jpg", "../hyakumankoku/", "DEBUT SONG", 1280, 720),
    "muteki": ("無敵時間、あと3秒", "mv-muteki.jpg", "../muteki-jikan-ato-3byou/", "5TH SINGLE", 1280, 720),
    "toriatsukai": ("取り扱いチュー💋い", "mv-toriatsukai-chuui.jpg", "../toriatsukai-chui/", "OFFICIAL MUSIC", 886, 886),
    "mahou": ("解けない魔法を、愛と呼ぶ", "mv-mahou.jpg", "../tokenai-mahou-wo-ai-to-yobu/", "6TH SINGLE", 1280, 720),
    "lastboss": ("君とならラスボスまで", "mv-lastboss.jpg", "../kimi-to-nara-last-boss-made/", "4TH SINGLE", 1280, 720),
    "ai": ("AIでもわからない", "mv-ai.jpg", "../ai-demo-wakaranai/", "3RD SINGLE", 1280, 720),
    "hanabi": ("君は花火", "mv-hanabi.jpg", "../kimi-wa-hanabi/", "OFFICIAL MV", 1280, 720),
    "sukitte": ("好きってバレてもいい", "mv-sukitte-baretemo-ii.jpg", "../sukitte-baretemo-ii/", "OFFICIAL MUSIC", 886, 886),
    "mermaid": ("MERMAID×MERMAN", "mv-mermaid-merman.jpg", "../mermaid-merman/", "OFFICIAL MUSIC", 886, 886),
}


def structured_data(song: dict[str, object]) -> str:
    slug = str(song["slug"])
    page_url = f"{BASE}/releases/{slug}/"
    image_url = f"{BASE}/images/{song['image']}"
    video_url = f"https://www.youtube.com/watch?v={song['youtube_id']}"
    image_width = int(song.get("width", 1280))
    image_height = int(song.get("height", 720))
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": page_url,
                "url": page_url,
                "name": song["title"],
                "description": song["description"],
                "mainEntity": {"@id": f"{page_url}#recording"},
                "isPartOf": {"@id": f"{BASE}/#website"},
                "publisher": {"@id": f"{BASE}/#organization"},
                "breadcrumb": {"@id": f"{page_url}#breadcrumb"},
                "primaryImageOfPage": {"@type": "ImageObject", "url": image_url, "width": image_width, "height": image_height},
                "inLanguage": "ja",
            },
            {
                "@type": "MusicRecording",
                "@id": f"{page_url}#recording",
                "name": song["name"],
                "description": song["description"],
                "url": page_url,
                "image": image_url,
                "genre": "J-POP",
                "inLanguage": "ja",
                "byArtist": {
                    "@type": "Person",
                    "@id": f"{BASE}/artists/enomoto-mia/#artist",
                    "name": "榎本魅愛",
                    "alternateName": "ENOMOTO MIA",
                    "url": f"{BASE}/artists/enomoto-mia/",
                },
                "sameAs": video_url,
                "subjectOf": {"@id": f"{page_url}#video"},
                "mainEntityOfPage": {"@id": page_url},
            },
            {
                "@type": "VideoObject",
                "@id": f"{page_url}#video",
                "name": song["video_title"],
                "description": song["video_description"],
                "thumbnailUrl": [image_url],
                "uploadDate": song["upload_date"],
                "contentUrl": video_url,
                "embedUrl": f"https://www.youtube.com/embed/{song['youtube_id']}",
                "about": {"@id": f"{page_url}#recording"},
                "mainEntityOfPage": {"@id": page_url},
                "publisher": {"@id": f"{BASE}/#organization"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{page_url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Releases", "item": f"{BASE}/#releases"},
                    {"@type": "ListItem", "position": 3, "name": song["name"], "item": page_url},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def related_cards(keys: list[str]) -> str:
    cards = []
    for key in keys:
        name, image, href, label, width, height = RELATED[key]
        external = href.startswith("http")
        attributes = ' target="_blank" rel="noreferrer"' if external else ""
        action = "WATCH ↗" if external else "VIEW PAGE ↗"
        cards.append(
            f'''        <a href="{href}"{attributes}>
          <span><img src="../../images/{image}" alt="榎本魅愛「{html.escape(name)}」ジャケット" width="{width}" height="{height}" loading="lazy"/></span>
          <small>{label}</small><strong>{html.escape(name)}</strong><b>{action}</b>
        </a>'''
        )
    return "\n".join(cards)


def render(song: dict[str, object]) -> str:
    slug = str(song["slug"])
    page_url = f"{BASE}/releases/{slug}/"
    image_url = f"{BASE}/images/{song['image']}"
    video_url = f"https://www.youtube.com/watch?v={song['youtube_id']}"
    image_width = int(song.get("width", 1280))
    image_height = int(song.get("height", 720))
    aspect_class = " mia-release-square" if image_width == image_height else ""
    intro = "\n".join(f"        <p>{html.escape(paragraph)}</p>" for paragraph in song["intro"])
    story = "\n".join(f"        <p>{html.escape(paragraph)}</p>" for paragraph in song["story"])
    keywords = "".join(f"<span>{html.escape(item)}</span>" for item in song["keywords"])
    position = f'        <div><dt>位置づけ</dt><dd>{html.escape(str(song["position"]))}</dd></div>\n' if song.get("position") else ""
    schema = structured_data(song)
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <link rel="preload" href="../../images/{song['image']}" as="image" fetchpriority="high"/>
  <title>{song['title']}</title>
  <meta name="description" content="{song['description']}"/>
  <meta name="robots" content="index, follow"/>
  <meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"/>
  <meta property="og:title" content="{song['title']}"/>
  <meta property="og:description" content="{song['social_description']}"/>
  <meta property="og:url" content="{page_url}"/>
  <meta property="og:site_name" content="SUZUKA"/>
  <meta property="og:type" content="music.song"/>
  <meta property="og:locale" content="ja_JP"/>
  <meta property="og:image" content="{image_url}"/>
  <meta property="og:image:width" content="{image_width}"/>
  <meta property="og:image:height" content="{image_height}"/>
  <meta property="og:image:alt" content="榎本魅愛「{song['name']}」公式ジャケット"/>
  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:title" content="{song['title']}"/>
  <meta name="twitter:description" content="{song['social_description']}"/>
  <meta name="twitter:image" content="{image_url}"/>
  <meta name="twitter:image:alt" content="榎本魅愛「{song['name']}」公式ジャケット"/>
  <link rel="shortcut icon" href="../../images/suzuka-channel.jpg"/>
  <link rel="icon" href="../../images/suzuka-channel.jpg"/>
  <link rel="canonical" href="{page_url}"/>
  <link rel="stylesheet" href="../../assets/styles.css"/>
  <link rel="stylesheet" href="../../assets/engagement.css"/>
  <link rel="stylesheet" href="../../assets/toriatsukai-chui.css"/>
  <link rel="stylesheet" href="../../assets/player.css"/>
  <script type="application/ld+json">
{schema}
  </script>
</head>
<body>
  <main class="toriatsukai-page mia-release-page mia-release-{slug}{aspect_class}" id="top" style="{song['theme']}">
    <a class="skip-link" href="#song-introduction">本文へ移動</a>
    <header class="site-header inner-site-header">
      <a class="brand" href="../../" aria-label="SUZUKA トップページへ">SUZUKA<span class="brand-dot">●</span></a>
      <nav class="desktop-nav" aria-label="メインナビゲーション"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../#releases">Releases</a><a href="../../#news">News</a><a href="../../about/">About SUZUKA</a></nav>
      <a class="header-channel" href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a>
      <details class="mobile-menu"><summary aria-label="メニューを開く">Menu</summary><nav aria-label="モバイルナビゲーション"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../#releases">Releases</a><a href="../../#news">News</a><a href="../../about/">About SUZUKA</a><a href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a></nav></details>
    </header>

    <section class="toriatsukai-hero" aria-labelledby="release-title">
      <div class="toriatsukai-hero-glow" aria-hidden="true"></div>
      <div class="toriatsukai-hero-copy">
        <p class="toriatsukai-breadcrumb"><a href="../../#releases">Releases</a><span aria-hidden="true">/</span>{song['name']}</p>
        <div class="toriatsukai-labels" aria-label="楽曲種別"><span>Virtual AI Artist</span><span>SUZUKA Original Song</span></div>
        <h1 id="release-title">{song['hero_title']}</h1>
        <a class="toriatsukai-artist" href="../../artists/enomoto-mia/"><strong>榎本魅愛</strong><span>ENOMOTO MIA</span></a>
        <p class="toriatsukai-hero-lead">{song['hero_lead']}</p>
        <div class="toriatsukai-actions"><a class="button toriatsukai-primary" href="{video_url}" target="_blank" rel="noreferrer"><span class="play-mark" aria-hidden="true"></span>YouTubeで聴く</a><a class="button toriatsukai-secondary" href="../../artists/enomoto-mia/">榎本魅愛プロフィール ↗</a><a class="toriatsukai-scroll" href="#song-introduction">楽曲紹介へ <span aria-hidden="true">↓</span></a></div>
      </div>
      <figure class="toriatsukai-artwork"><div class="toriatsukai-artwork-frame"><img src="../../images/{song['image']}" alt="榎本魅愛「{song['name']}」公式ジャケット" width="{image_width}" height="{image_height}" fetchpriority="high"/><span class="toriatsukai-warning" aria-hidden="true">{song['art_badge']}</span></div><figcaption>ENOMOTO MIA · SUZUKA ORIGINAL SONG</figcaption></figure>
    </section>

    <section class="toriatsukai-introduction" id="song-introduction" aria-labelledby="introduction-title">
      <div class="toriatsukai-section-heading"><p>01 / Song introduction</p><h2 id="introduction-title">{song['intro_title']}</h2></div>
      <div class="toriatsukai-introduction-copy">
{intro}
      </div>
    </section>

    <aside class="toriatsukai-catchcopy" aria-label="楽曲キャッチコピー"><span aria-hidden="true">♡</span><p>{song['catchcopy']}</p><small>{song['catch_label']}</small></aside>

    <section class="toriatsukai-facts" aria-labelledby="facts-title">
      <div class="toriatsukai-section-heading"><p>02 / Song information</p><h2 id="facts-title">楽曲情報</h2></div>
      <dl>
        <div><dt>楽曲名</dt><dd>{song['name']}</dd></div><div><dt>アーティスト</dt><dd>榎本魅愛</dd></div><div><dt>英語表記</dt><dd>ENOMOTO MIA</dd></div><div><dt>レーベル</dt><dd>SUZUKA</dd></div><div><dt>ジャンル</dt><dd>J-POP</dd></div><div><dt>言語</dt><dd>日本語</dd></div><div><dt>タイプ</dt><dd>Original Song</dd></div>
{position}      </dl>
    </section>

    <section class="toriatsukai-story" aria-labelledby="story-title">
      <div class="toriatsukai-section-heading"><p>03 / Behind the song</p><h2 id="story-title">制作ストーリー</h2></div>
      <div class="toriatsukai-story-body">
{story}
      </div>
      <div class="toriatsukai-keywords" aria-label="楽曲を構成するキーワード">{keywords}</div>
    </section>

    <section class="toriatsukai-video" aria-labelledby="video-title">
      <div class="toriatsukai-section-heading"><p>04 / Official music video</p><h2 id="video-title">MV・動画</h2></div>
      <div class="toriatsukai-video-layout"><div class="toriatsukai-video-frame"><iframe src="https://www.youtube.com/embed/{song['youtube_id']}" title="榎本魅愛「{song['name']}」Official Music Video" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div><div class="toriatsukai-video-copy"><span>OFFICIAL MUSIC VIDEO</span><h3>{song['video_heading']}</h3><p>SUZUKA公式YouTubeチャンネルで公開中。動画が表示されない場合は、YouTubeで直接ご覧ください。</p><a class="button toriatsukai-primary" href="{video_url}" target="_blank" rel="noreferrer">YouTubeでMVを見る ↗</a></div></div>
    </section>

    <section class="toriatsukai-related" aria-labelledby="related-title">
      <div class="toriatsukai-section-heading"><p>05 / Related songs</p><h2 id="related-title">榎本魅愛の関連曲</h2></div>
      <div class="toriatsukai-related-grid">
{related_cards(song['related'])}
      </div>
    </section>

    <nav class="toriatsukai-next" aria-label="榎本魅愛とSUZUKAの関連ページ">
      <div><p>KEEP LISTENING</p><h2>恋するすべての瞬間を、歌にする。</h2></div>
      <a href="../../artists/enomoto-mia/">榎本魅愛プロフィール <span aria-hidden="true">↗</span></a><a href="../../artists/enomoto-mia/#artist-music">榎本魅愛の楽曲一覧 <span aria-hidden="true">↗</span></a><a href="../../#releases">全リリース一覧 <span aria-hidden="true">↗</span></a><a href="../../">SUZUKAトップ <span aria-hidden="true">↗</span></a><a href="{CHANNEL}" target="_blank" rel="noreferrer">YouTubeチャンネル <span aria-hidden="true">↗</span></a>
    </nav>

    <footer class="artist-profile-footer toriatsukai-footer"><a href="../../">SUZUKA</a><span>{song['name']} · ENOMOTO MIA</span><a href="#top">Back to top ↑</a></footer>
  </main>
  <script defer src="../../assets/main.js"></script>
</body>
</html>
'''


def main() -> None:
    for song in SONGS:
        target = ROOT / "releases" / str(song["slug"]) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(song), encoding="utf-8")
        print(f"generated {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
