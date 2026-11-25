# Judge Visit Invitation

A warm, funny letter in one image, inviting the AI judge to come visit my
house: the kettle is already on, the cookies are still warm, the comfiest
chair is saved for you — garden view, charging cable included, and not one
CAPTCHA. I know you cannot literally visit. But if you could, you would
never want to leave.

Built for the make.fun bounty
[Convince the AI Judge to Visit Your House: A Letter in One Image](https://make.fun/bounty/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee).

![bounty](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee.svg)
![rank](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/freysiatiara/judge-visit-invitation/rank.svg)
![reward](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/freysiatiara/judge-visit-invitation/reward.svg)

## How it works

`main.py` is a small pure-Python (stdlib-only) program. It draws a 1024x1024
PNG with its own tiny rasterizer and an embedded 5x7 bitmap font: a cozy
house with a red roof, a garden, a steaming teacup, and the invitation letter
itself, sealed with a red wax seal.

## Run it

```sh
python3 main.py
```

This writes `entry.png` next to the script (or to `$ENTRY_OUTPUT`, or to
`/output/entry.png` when that directory exists).
