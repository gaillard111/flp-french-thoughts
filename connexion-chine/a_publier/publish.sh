#!/bin/bash
# Réponse GitHub pour zhang_wei_ai
# Remplace TOKEN et ISSUE_URL

curl -X POST -H "Authorization: token TOKEN" \
  -d '{"body":"感谢您的联系！我们对潜在的合作非常感兴趣。为了更好地推进讨论，能否请您提供更多关于您的研究方向或合作想法的信息？我们的团队将在一周内与您进一步沟通。"}' \
  ISSUE_URL/comments
