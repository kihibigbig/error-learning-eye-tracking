"""Keep upstream unchanged; add an explicit paused-calibration bridge to a lab-only copy."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
source=root.parent/'lib/webgazer.js'
anchor='src_webgazer.getCurrentPrediction = function() {'
bridge='''// BEGIN LOCAL PAUSED CALIBRATION BRIDGE (2026-10-02)
// getCurrentPrediction refreshes latestEyeFeatures while paused, but the upstream
// recordScreenPosition silently ignores paused calls. This explicit API registers
// the just-extracted features without starting a concurrent prediction loop.
src_webgazer.recordCalibrationPoint = function(x, y) {
  if (!paused) throw new Error('Calibration bridge requires paused inference');
  if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('Invalid calibration target');
  var before = regs.map(function(r) { return r.getData().length; });
  if (latestEyeFeatures) {
    regs.forEach(function(r) { r.addData(latestEyeFeatures, [x, y], 'click'); });
  }
  var accepted = regs.map(function(r, i) { return r.getData().length - before[i]; });
  return { eyeFeaturesReady: !!latestEyeFeatures, accepted: accepted.length ? Math.min.apply(null, accepted) : 0, modelCounts: regs.map(function(r) { return r.getData().length; }) };
};
src_webgazer.getCalibrationState = function() {
  return { paused: paused, eyeFeaturesReady: !!latestEyeFeatures, modelCounts: regs.map(function(r) { return r.getData().length; }) };
};
// END LOCAL PAUSED CALIBRATION BRIDGE
'''
text=source.read_text(encoding='utf-8')
assert text.count(anchor)==1
output=root/'webgazer-calibration.js'
output.write_text(text.replace(anchor,bridge+'\n'+anchor),encoding='utf-8')
(root/'bridge_provenance.json').write_text(json.dumps({'upstream_file':'../lib/webgazer.js','upstream_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'modification':'Add explicit recordCalibrationPoint and getCalibrationState; upstream APIs unchanged; GPL-3.0 retained','date':'2026-10-02'},indent=2),encoding='utf-8')
print('Built lab-only bridge; upstream unchanged')
