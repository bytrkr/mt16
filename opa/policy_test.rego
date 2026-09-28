package mt16

test_allow_all_claims_ok {
  decision.allow with input as {
    "claims": [
      {"claim":"c1","claim_type":"general","verification_score":0.90,"sources_count":2,"flags":[], "sources":[{"category":"news"}]},
      {"claim":"c2","claim_type":"economy","verification_score":0.92,"sources_count":2,"flags":[], "sources":[{"category":"regulator"}]}
    ]
  }
}

test_block_low_score {
  not decision.allow with input as {
    "claims": [
      {"claim":"c1","claim_type":"general","verification_score":0.10,"sources_count":2,"flags":[], "sources":[{"category":"news"}]}
    ]
  }
  decision.reason == "LOW_VERIFICATION_SCORE" with input as {
    "claims": [
      {"claim":"c1","claim_type":"general","verification_score":0.10,"sources_count":2,"flags":[], "sources":[{"category":"news"}]}
    ]
  }
}

test_block_manipulation {
  not decision.allow with input as {
    "claims": [
      {"claim":"c1","claim_type":"general","verification_score":0.90,"sources_count":2,"flags":["MANIPULATION_RISK"], "sources":[{"category":"news"}]}
    ]
  }
}

test_block_missing_authoritative_source_for_economy {
  not decision.allow with input as {
    "claims": [
      {"claim":"c1","claim_type":"economy","verification_score":0.90,"sources_count":2,"flags":[], "sources":[{"category":"news"}]}
    ]
  }
  decision.reason == "MISSING_AUTHORITATIVE_SOURCE" with input as {
    "claims": [
      {"claim":"c1","claim_type":"economy","verification_score":0.90,"sources_count":2,"flags":[], "sources":[{"category":"news"}]}
    ]
  }
}
