"""Weather presets for the game packs (day/night/rain/snow skyboxes and env XML).

Run by launcher.exe with the bundled Python (Runtime\\python):
    python weather_packs.py <root_dir> <game_dir> <runtime_dir> <mode>
Same code the old Python launcher ran in-process (run_launcher.py), moved here
unchanged so the C# launcher does not need its own NPK writer.
"""
import json
import os
import subprocess
import sys
import threading
import time

ROOT_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(ROOT_DIR, "game")
RUNTIME_DIR = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(ROOT_DIR, "client", "runtime")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def is_process_running(proc_name, max_age=0):
    try:
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq %s" % proc_name],
                                      creationflags=0x08000000, text=True, errors="ignore")
        return proc_name.lower() in out.lower()
    except Exception:
        return False

_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "255,90,120,170"
      DIRLightIntensity = "0.25"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,4,8,16"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "0.80"
      AOFactor = "0.30"
      Ambient = "0.18,0.22,0.30,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.22,0.26,0.36,1"
      EnvUE4SHR = "-0.005,0.006,0.018,0.016"
      EnvUE4SHG = "-0.007,0.008,0.022,0.019"
      EnvUE4SHB = "-0.010,0.010,0.028,0.022">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,14,24,46"
        DistantColor = "0,10,18,34"
        Start = "80"
        End = "600"
        Distant = "3500"
        ShaderDensity = "2.2"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,14,24,46"
        U4FogHeight = "5000"
        U4FogDensity = "0.048"
        U4FogHeightFalloff = "0.95"
        U4StartDistance = "90"
        U4MaxOpacity = "0.94"
        U4FogDirInscatteringColor = "255,22,35,68"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "400"
        U4SkyRate = "0.04" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.02" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.5" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.9" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "3" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.09" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.98" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.05" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "5" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "25" />
        <background_intensity Value = "0.12" />
        <cloud_speed Value = "0.5" />
        <low_cloud_pow Value = "1.5" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.012,0.020,0.045,1.0" />
        <ZenithColor Value = "0.003,0.006,0.015,1.0" />
        <overrall_color Value = "0.05,0.08,0.15,0.2" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.10,0.15,0.25,1" />
        <WaterColorDeep Value = "0.02,0.04,0.08,0" />
        <WaterColorShallow Value = "0.03,0.05,0.10,0.6" />
        <low_water_base_color Value = "0.05,0.08,0.15,0.7" />
        <shallowColor Value = "0.08,0.12,0.20,0.5" />
        <specColor Value = "0.15,0.25,0.40,0.3" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_DAWN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.75,-0.35,-0.55"
      DIRLightColor = "255,255,215,190"
      DIRLightIntensity = "2.3"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,210,145,130"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.62,0.55,0.60,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.75,0.70,0.65,1"
      EnvUE4SHR = "-0.015,0.025,0.080,0.070"
      EnvUE4SHG = "-0.022,0.020,0.075,0.060"
      EnvUE4SHB = "-0.025,0.018,0.085,0.065">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,230,175,160"
        DistantColor = "0,190,140,135"
        Start = "280"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,230,175,160"
        U4FogHeight = "4500"
        U4FogDensity = "0.009"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "500"
        U4MaxOpacity = "0.85"
        U4FogDirInscatteringColor = "255,255,200,170"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.2" Size = "1.5" FlareColor = "1.0,0.85,0.75,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.25" Size = "0.35" FlareColor = "1.0,0.9,0.8,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.5" Size = "0.35" FlareColor = "1.0,0.85,0.7,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.15" Size = "0.8" FlareColor = "1.0,0.8,0.7,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "1.5" Size = "1.0" FlareColor = "0.8,0.5,0.4,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.1" Size = "0.4" FlareColor = "0.9,0.7,0.5,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.15" Size = "0.3" FlareColor = "1.0,0.6,0.5,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.3" Size = "0.5" FlareColor = "1.0,0.9,0.8,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "20" />
        <background_intensity Value = "1.0" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.1" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.98,0.62,0.50,1.0" />
        <ZenithColor Value = "0.18,0.22,0.42,1.0" />
        <overrall_color Value = "0.95,0.70,0.60,0.35" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.6,0.45,0.50,1" />
        <WaterColorDeep Value = "0.15,0.10,0.18,0" />
        <WaterColorShallow Value = "0.35,0.25,0.30,0.65" />
        <low_water_base_color Value = "0.50,0.40,0.45,0.75" />
        <shallowColor Value = "0.75,0.55,0.50,0.5" />
        <specColor Value = "0.90,0.75,0.65,0.4" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SUNSET_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.85,-0.22,-0.45"
      DIRLightColor = "255,255,125,35"
      DIRLightIntensity = "2.4"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,180,75,30"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.58,0.45,0.38,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.75,0.60,0.45,1"
      EnvUE4SHR = "-0.010,0.030,0.095,0.080"
      EnvUE4SHG = "-0.018,0.015,0.055,0.045"
      EnvUE4SHB = "-0.028,0.010,0.040,0.035">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,190,85,30"
        DistantColor = "0,150,65,25"
        Start = "250"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,190,85,30"
        U4FogHeight = "4500"
        U4FogDensity = "0.01"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "500"
        U4MaxOpacity = "0.88"
        U4FogDirInscatteringColor = "255,255,110,25"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.6" Size = "1.8" FlareColor = "1.0,0.6,0.2,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "1.0,0.7,0.3,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "1.0,0.5,0.2,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1.0" FlareColor = "1.0,0.4,0.1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2.0" Size = "1.3" FlareColor = "0.7,0.3,0.1,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.12" Size = "0.5" FlareColor = "0.9,0.5,0.2,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "1.0,0.35,0.1,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "1.0,0.7,0.3,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "1.1" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.0" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "1.0,0.38,0.06,1.0" />
        <ZenithColor Value = "0.08,0.10,0.28,1.0" />
        <overrall_color Value = "1.0,0.48,0.12,0.45" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.65,0.35,0.20,1" />
        <WaterColorDeep Value = "0.18,0.08,0.05,0" />
        <WaterColorShallow Value = "0.40,0.20,0.10,0.65" />
        <low_water_base_color Value = "0.55,0.30,0.15,0.75" />
        <shallowColor Value = "0.80,0.45,0.20,0.5" />
        <specColor Value = "1.0,0.70,0.30,0.5" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_AUTUMN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.85,-0.22,-0.45"
      DIRLightColor = "255,250,135,28"
      DIRLightIntensity = "2.6"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,200,85,25"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.9"
      AOFactor = "0.33"
      Ambient = "0.72,0.48,0.22,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.85,0.65,0.40,1"
      EnvUE4SHR = "-0.010,0.035,0.110,0.090"
      EnvUE4SHG = "-0.018,0.018,0.065,0.050"
      EnvUE4SHB = "-0.028,0.010,0.035,0.030">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,205,95,25"
        DistantColor = "0,165,75,20"
        Start = "250"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,205,95,25"
        U4FogHeight = "4500"
        U4FogDensity = "0.012"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "400"
        U4MaxOpacity = "0.88"
        U4FogDirInscatteringColor = "255,255,120,20"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.8" Size = "2.0" FlareColor = "1.0,0.65,0.18,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "1.0,0.75,0.25,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "1.0,0.55,0.18,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1.0" FlareColor = "1.0,0.45,0.12,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2.0" Size = "1.3" FlareColor = "0.75,0.35,0.1,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.12" Size = "0.5" FlareColor = "0.95,0.55,0.18,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "1.0,0.38,0.1,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "1.0,0.75,0.25,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "1.15" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.0" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "1.0,0.42,0.06,1.0" />
        <ZenithColor Value = "0.10,0.08,0.24,1.0" />
        <overrall_color Value = "1.0,0.52,0.14,0.55" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.68,0.38,0.18,1" />
        <WaterColorDeep Value = "0.20,0.08,0.04,0" />
        <WaterColorShallow Value = "0.42,0.22,0.08,0.65" />
        <low_water_base_color Value = "0.55,0.28,0.12,0.75" />
        <shallowColor Value = "0.70,0.38,0.18,0.45" />
        <specColor Value = "1.0,0.70,0.30,0.85" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_DAY_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.1269,-0.738,-0.6628"
      DIRLightColor = "255,227,217,199"
      DIRLightIntensity = "2.7"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,98,116,144"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.549,0.5686,0.6667,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.7451,0.7412,0.6235,1"
      EnvUE4SHR = "-0.0218,0.0213,0.0718,0.0618"
      EnvUE4SHG = "-0.0288,0.0233,0.0809,0.0653"
      EnvUE4SHB = "-0.0333,0.0269,0.093,0.067">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,159,199,247"
        DistantColor = "0,136,136,136"
        Start = "300"
        End = "1000"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,70,105,181"
        U4FogHeight = "4500"
        U4FogDensity = "0.01"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "600"
        U4MaxOpacity = "1"
        U4FogDirInscatteringColor = "255,105,131,225"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.5" Size = "1.7" FlareColor = "0.9276,0.5608,0.4275,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "0.9824,1,1,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "0.998,1,1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1" FlareColor = "0.998,1,1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2" Size = "1.2" FlareColor = "0.1252,0.1922,0.2902,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.1" Size = "0.5" FlareColor = "0.1644,0.6471,0.2235,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "0.9785,0.2824,0.2824,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "0.998,1,1,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "20" />
        <background_intensity Value = "1" />
        <cloud_speed Value = "2" />
        <low_cloud_pow Value = "0.86" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.5294,0.6824,0.9804,1" />
        <ZenithColor Value = "0.1412,0.2314,0.6902,1" />
        <overrall_color Value = "0.8157,0.8745,0.9098,0.1137" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "1,1,1,1" />
        <WaterColorDeep Value = "0.3569,0.3686,0.3804,0" />
        <WaterColorShallow Value = "0.1608,0.1922,0.2314,0.6902" />
        <low_water_base_color Value = "0.5294,0.6667,0.7686,0.7569" />
        <shallowColor Value = "0.9765,0.8235,0.6431,0.4902" />
        <specColor Value = "0.3137,0.4902,0.6275,0.2078" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_RAIN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.15,-0.85,-0.50"
      DIRLightColor = "200,140,150,165"
      DIRLightIntensity = "0.75"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,65,72,80"
      WeatherIntensity0 = "1.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.0"
      EnvExposure = "1.6"
      AOFactor = "0.45"
      Ambient = "0.32,0.35,0.39,1"
      EnvExposureMetallic = "1.6"
      AmbientMetallic = "0.45,0.48,0.52,1"
      EnvUE4SHR = "-0.015,0.015,0.045,0.040"
      EnvUE4SHG = "-0.018,0.016,0.050,0.042"
      EnvUE4SHB = "-0.022,0.018,0.060,0.048">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,70,78,88"
        DistantColor = "0,55,62,70"
        Start = "150"
        End = "800"
        Distant = "4500"
        ShaderDensity = "1.5"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,65,74,85"
        U4FogHeight = "3500"
        U4FogDensity = "0.035"
        U4FogHeightFalloff = "1.5"
        U4StartDistance = "200"
        U4MaxOpacity = "1.0"
        U4FogDirInscatteringColor = "255,80,90,105"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "600"
        U4SkyRate = "0.05" />
      <SkyParamFloat>
        <HorizonFalloff Value = "12" />
        <background_intensity Value = "0.45" />
        <cloud_speed Value = "5.5" />
        <low_cloud_pow Value = "1.25" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.38,0.42,0.46,1.0" />
        <ZenithColor Value = "0.18,0.22,0.26,1.0" />
        <overrall_color Value = "0.35,0.38,0.42,0.85" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.4,0.45,0.5,1" />
        <WaterColorDeep Value = "0.15,0.18,0.22,0" />
        <WaterColorShallow Value = "0.22,0.26,0.30,0.85" />
        <low_water_base_color Value = "0.35,0.40,0.45,0.8" />
        <shallowColor Value = "0.5,0.55,0.6,0.6" />
        <specColor Value = "0.9,0.95,1.0,0.7" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_RAINY_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "200,90,125,185"
      DIRLightIntensity = "0.38"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,4,8,16"
      WeatherIntensity0 = "1.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.0"
      EnvExposure = "1.10"
      AOFactor = "0.35"
      Ambient = "0.16,0.20,0.28,1"
      EnvExposureMetallic = "1.20"
      AmbientMetallic = "0.26,0.32,0.44,1"
      EnvUE4SHR = "-0.006,0.008,0.022,0.020"
      EnvUE4SHG = "-0.009,0.010,0.026,0.022"
      EnvUE4SHB = "-0.012,0.012,0.034,0.028">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,20,32,54"
        DistantColor = "0,14,24,40"
        Start = "45"
        End = "450"
        Distant = "2800"
        ShaderDensity = "2.8"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,18,30,50"
        U4FogHeight = "5200"
        U4FogDensity = "0.068"
        U4FogHeightFalloff = "0.90"
        U4StartDistance = "50"
        U4MaxOpacity = "0.97"
        U4FogDirInscatteringColor = "255,28,42,75"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "300"
        U4SkyRate = "0.05" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.02" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.5" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.9" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "3" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.09" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.98" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.05" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "5" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "22" />
        <background_intensity Value = "0.25" />
        <cloud_speed Value = "5.0" />
        <low_cloud_pow Value = "1.3" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.015,0.025,0.055,1.0" />
        <ZenithColor Value = "0.005,0.008,0.020,1.0" />
        <overrall_color Value = "0.06,0.10,0.20,0.3" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.12,0.18,0.30,1" />
        <WaterColorDeep Value = "0.03,0.05,0.10,0" />
        <WaterColorShallow Value = "0.05,0.08,0.15,0.7" />
        <low_water_base_color Value = "0.08,0.12,0.22,0.8" />
        <shallowColor Value = "0.10,0.16,0.28,0.5" />
        <specColor Value = "0.75,0.85,1.0,0.6" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SNOW_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.28,-0.92,-0.28"
      DIRLightColor = "255,235,242,255"
      DIRLightIntensity = "0.95"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,190,210,230"
      WeatherIntensity0 = "0.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.95"
      EnvExposure = "1.25"
      AOFactor = "0.20"
      Ambient = "0.82,0.88,0.96,1"
      EnvExposureMetallic = "1.30"
      AmbientMetallic = "0.88,0.94,1.0,1"
      EnvUE4SHR = "-0.015,0.020,0.035,0.030"
      EnvUE4SHG = "-0.018,0.024,0.040,0.035"
      EnvUE4SHB = "-0.022,0.030,0.050,0.045">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,210,225,240"
        DistantColor = "0,185,205,225"
        Start = "250"
        End = "1400"
        Distant = "6000"
        ShaderDensity = "1.2"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,215,230,245"
        U4FogHeight = "4000"
        U4FogDensity = "0.018"
        U4FogHeightFalloff = "1.0"
        U4StartDistance = "300"
        U4MaxOpacity = "0.80"
        U4FogDirInscatteringColor = "255,240,248,255"
        U4DirInscatteringE = "12"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.05" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "0.85" />
        <cloud_speed Value = "3.0" />
        <low_cloud_pow Value = "1.1" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.78,0.85,0.92,1.0" />
        <ZenithColor Value = "0.65,0.75,0.88,1.0" />
        <overrall_color Value = "0.85,0.90,0.98,0.8" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.55,0.65,0.75,1" />
        <WaterColorDeep Value = "0.20,0.30,0.45,0" />
        <WaterColorShallow Value = "0.45,0.55,0.68,0.7" />
        <low_water_base_color Value = "0.40,0.50,0.65,0.8" />
        <shallowColor Value = "0.50,0.60,0.72,0.5" />
        <specColor Value = "0.90,0.95,1.0,0.9" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SNOWY_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "220,120,165,225"
      DIRLightIntensity = "0.45"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,10,18,30"
      WeatherIntensity0 = "0.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.95"
      EnvExposure = "1.15"
      AOFactor = "0.25"
      Ambient = "0.22,0.30,0.44,1"
      EnvExposureMetallic = "1.25"
      AmbientMetallic = "0.32,0.42,0.58,1"
      EnvUE4SHR = "-0.008,0.010,0.026,0.024"
      EnvUE4SHG = "-0.011,0.014,0.032,0.028"
      EnvUE4SHB = "-0.015,0.018,0.042,0.036">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,14,24,42"
        DistantColor = "0,8,16,30"
        Start = "200"
        End = "1000"
        Distant = "5000"
        ShaderDensity = "1.3"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,16,28,48"
        U4FogHeight = "4000"
        U4FogDensity = "0.020"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "250"
        U4MaxOpacity = "0.85"
        U4FogDirInscatteringColor = "255,20,35,60"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "900"
        U4SkyRate = "0.04" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "22" />
        <background_intensity Value = "0.30" />
        <cloud_speed Value = "4.0" />
        <low_cloud_pow Value = "1.3" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.020,0.035,0.070,1.0" />
        <ZenithColor Value = "0.008,0.012,0.028,1.0" />
        <overrall_color Value = "0.08,0.14,0.26,0.4" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.15,0.22,0.36,1" />
        <WaterColorDeep Value = "0.04,0.07,0.14,0" />
        <WaterColorShallow Value = "0.08,0.12,0.22,0.7" />
        <low_water_base_color Value = "0.10,0.16,0.28,0.8" />
        <shallowColor Value = "0.14,0.22,0.36,0.5" />
        <specColor Value = "0.80,0.90,1.0,0.7" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

def _ensure_rain_skybox(game_dir):
    try:
        rain_dds = os.path.join(game_dir, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_rain.dds')
        day_dds = os.path.join(game_dir, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        if os.path.isfile(rain_dds) and os.path.getsize(rain_dds) > 1000:
            return rain_dds
        if not os.path.isfile(day_dds):
            return None
        with open(day_dds, 'rb') as f:
            hdr = f.read(128)
            raw = bytearray(f.read())
        for i in range(0, len(raw), 4):
            b = raw[i]; g = raw[i+1]; r = raw[i+2]
            y = (r * 77 + g * 150 + b * 29) >> 8
            raw[i]   = min(255, (y * 215) >> 8)
            raw[i+1] = min(255, (y * 200) >> 8)
            raw[i+2] = min(255, (y * 190) >> 8)
        os.makedirs(os.path.dirname(rain_dds), exist_ok=True)
        with open(rain_dds, 'wb') as f:
            f.write(hdr)
            f.write(raw)
        return rain_dds
    except Exception:
        return None

def _get_env_xml(mode):
    m = (mode or "").lower()
    if m == "night":
        return _NIGHT_ENV_XML
    elif m in ("rainy_night", "rainynight", "rain_night", "darkrain", "stormynight"):
        return _RAINY_NIGHT_ENV_XML
    elif m in ("snowy_night", "snowynight", "snow_night", "winternight"):
        return _SNOWY_NIGHT_ENV_XML
    elif m in ("snow", "snowy", "winter"):
        return _SNOW_ENV_XML
    elif m == "dawn":
        return _DAWN_ENV_XML
    elif m == "sunset":
        return _SUNSET_ENV_XML
    elif m in ("autumn", "fall", "harvest"):
        return _AUTUMN_ENV_XML
    elif m == "rain":
        return _RAIN_ENV_XML
    else:
        return _DAY_ENV_XML

def _normalize_env_mode(target_mode):
    if isinstance(target_mode, bool):
        return "night" if target_mode else "day"
    if not isinstance(target_mode, str) or target_mode.lower() not in (
            "auto", "day", "dawn", "sunset", "autumn", "night", "rain",
            "rainy_night", "snow", "snowy_night"):
        return "day" if not bool(target_mode) else "night"
    if target_mode.lower() == "auto":
        return "day"
    return target_mode.lower()


_ENV_NPK_STATE = os.path.join(RUNTIME_DIR, "env_npk_state.json")
_ENV_NPK_LOCK = threading.Lock()


def _atomic_copy(src, dst):
    tmp = dst + ".tmp_navy"
    import shutil
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def _restore_day_packs():
    """Put every pack/file the weather feature touched back to its original.

    'day' used to REBUILD Documents/res/common.npk from scratch (every entry
    decompressed, new offsets) and rewrite world4k.npk's index on every Play,
    while the pack's .info_ext still described the original layout. NeoX
    mounts Documents/ ahead of game/, so a bad rebuild there is read first.
    Restoring the pristine byte-for-byte backup removes that risk entirely.
    """
    docs_res = os.path.join(GAME_DIR, "Documents", "res")
    for rel in ("common.npk", os.path.join("levelsets", "4k_diedai.npk")):
        cur = os.path.join(docs_res, rel)
        bak = cur + ".orig_day"
        if os.path.isfile(bak):
            try:
                if (not os.path.isfile(cur)
                        or os.path.getsize(cur) != os.path.getsize(bak)
                        or _file_digest(cur) != _file_digest(bak)):
                    _atomic_copy(bak, cur)
                    print("restored original %s" % rel)
            except Exception as e:
                print("restore %s failed: %s" % (rel, e))
    # Loose overrides this launcher generated (never shipped with the game).
    loose = [os.path.join(docs_res, "levelsets", "4k_diedai", "skybox_diedai01.dds")]
    generated_xml = set()
    for m in ("day", "night", "rain", "rainy_night", "snow", "snowy_night", "dawn", "sunset", "autumn"):
        try:
            generated_xml.add(_get_env_xml(m).strip().encode("utf-8"))
        except Exception:
            pass
    for base in (os.path.join(GAME_DIR, "Documents", "res", "scene"), os.path.join(GAME_DIR, "res", "scene")):
        for sub in (os.path.join("world4k", "world4k_content"), "world4k_content"):
            for name in ("high.xml", "tiaosan.xml", "low.xml"):
                xp = os.path.join(base, sub, "env_info", name)
                try:
                    if os.path.isfile(xp):
                        with open(xp, "rb") as fh:
                            if fh.read().strip() in generated_xml:
                                loose.append(xp)
                except Exception:
                    pass
    for lp in loose:
        try:
            if os.path.isfile(lp):
                os.remove(lp)
        except Exception as e:
            print("remove %s failed: %s" % (lp, e))


def _file_digest(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _apply_day_night_npk_files_async(target_mode):
    """Settings save: rebuild the weather packs off the UI thread (a mode
    change rewrites a ~450 MB world4k.npk). Play waits for it to finish."""
    t = threading.Thread(target=_apply_day_night_npk_files, args=(target_mode,), daemon=True)
    t.start()
    return t


def _wait_env_npk_idle(timeout=600.0):
    """Block until a background weather-pack rebuild is done."""
    if _ENV_NPK_LOCK.acquire(True, timeout):
        _ENV_NPK_LOCK.release()


def _apply_day_night_npk_files(target_mode):
    """Apply the launcher weather preset to the game packs - safely.

    * never while client.exe is running (it has these packs open; rewriting
      one under it is a native crash in the XML/texture loader)
    * only when the mode actually changes (it used to rewrite a 450 MB
      world4k.npk and rebuild common.npk on every Play and every settings save)
    * 'day'/'auto' restores the original files instead of rebuilding them
    """
    mode = _normalize_env_mode(target_mode)
    if not _ENV_NPK_LOCK.acquire(False):
        return
    try:
        if is_process_running("client.exe", max_age=0):
            print("weather packs: client.exe is running - change applies next launch")
            return
        prev = None
        try:
            with open(_ENV_NPK_STATE, "r", encoding="utf-8") as fh:
                prev = (json.load(fh) or {}).get("mode")
        except Exception:
            prev = None
        if prev == mode:
            return
        if mode == "day":
            _restore_day_packs()
            if prev not in (None, "day") or os.path.isfile(
                    os.path.join(GAME_DIR, "Documents", "res", "scene", "world4k.npk.orig_day_xmls")):
                _apply_day_night_npk_files_impl("day", world4k_only=True)
        else:
            _apply_day_night_npk_files_impl(mode)
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            with open(_ENV_NPK_STATE, "w", encoding="utf-8") as fh:
                json.dump({"mode": mode, "updated": time.time()}, fh)
        except Exception:
            pass
    finally:
        _ENV_NPK_LOCK.release()


def _apply_day_night_npk_files_impl(target_mode, world4k_only=False):
    import struct, zlib, shutil
    HEADER = struct.Struct('<4s5I')
    RECORD = struct.Struct('<6I2H')

    if isinstance(target_mode, bool):
        mode = "night" if target_mode else "day"
    elif not isinstance(target_mode, str) or target_mode.lower() not in ("auto", "day", "dawn", "sunset", "autumn", "night", "rain", "rainy_night", "snow", "snowy_night"):
        mode = "day" if not bool(target_mode) else "night"
    elif target_mode.lower() == "auto":
        mode = "day"
    else:
        mode = target_mode.lower()

    is_night = (mode in ("night", "rainy_night", "snowy_night"))
    is_rain = (mode in ("rain", "rainy_night"))
    is_snow = (mode in ("snow", "snowy_night"))

    def _build_npk(out_path, entries_dict):
        names = list(entries_dict.keys())
        data_blobs = [entries_dict[n] for n in names]
        file_count = len(names)
        off = HEADER.size
        records = []
        file_data = b''.join(data_blobs)
        for b in data_blobs:
            clen = len(b); olen = clen
            crc = zlib.crc32(b) & 0xffffffff
            records.append(RECORD.pack(0, off, clen, olen, crc, crc, 0, 0))
            off += clen
        hdr = HEADER.pack(b'NXPK', file_count, 0, 0, 2, off)
        index_bytes = b''.join(records)
        names_bytes = b''.join([n.encode('utf-8') + b'\x00' for n in names])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        tmp_path = out_path + '.tmp_navy'
        with open(tmp_path, 'wb') as f:
            f.write(hdr); f.write(file_data); f.write(index_bytes); f.write(names_bytes)
        os.replace(tmp_path, out_path)  # never leave a half-written pack behind

    def _resolve_target_pack(rel_subpath):
        doc_p = os.path.join(GAME_DIR, 'Documents', 'res', rel_subpath)
        base_p = os.path.join(GAME_DIR, 'res', rel_subpath)
        if os.path.isfile(doc_p):
            return doc_p
        if os.path.isfile(base_p):
            try:
                os.makedirs(os.path.dirname(doc_p), exist_ok=True)
                shutil.copyfile(base_p, doc_p)
                return doc_p
            except Exception:
                return base_p
        return None

    # 1. 4k_diedai.npk (injects the starry skybox in night, overcast gray in rain, day for others)
    pk_4k_path = None if world4k_only else _resolve_target_pack(os.path.join('levelsets', '4k_diedai.npk'))
    if pk_4k_path:
        pk_4k_bak = pk_4k_path + '.orig_day'
        if os.path.isfile(pk_4k_path) and not os.path.isfile(pk_4k_bak):
            try: shutil.copyfile(pk_4k_path, pk_4k_bak)
            except Exception: pass

        if is_night:
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_night.dds')
        elif is_rain:
            _ensure_rain_skybox(GAME_DIR)
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_rain.dds')
            if not os.path.isfile(sky_src):
                sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        else:
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        if os.path.isfile(sky_src):
            try:
                with open(sky_src, 'rb') as f: sky_bytes = f.read()
                sig_bytes = b'levelsets_4k_diedai_signature\x00'
                if os.path.isfile(pk_4k_bak):
                    try:
                        import tools.npk as _npk
                        pk = _npk.Pack(pk_4k_bak)
                        hits = pk.find('levelsets_4k_diedai_signature')
                        if hits: sig_bytes = hits[0].raw()
                    except Exception: pass
                _build_npk(pk_4k_path, {
                    'levelsets_4k_diedai_signature': sig_bytes,
                    'skybox_diedai01.dds': sky_bytes
                })
                dst_loose = os.path.join(GAME_DIR, 'Documents', 'res', 'levelsets', '4k_diedai', 'skybox_diedai01.dds')
                os.makedirs(os.path.dirname(dst_loose), exist_ok=True)
                shutil.copyfile(sky_src, dst_loose)
            except Exception as e:
                print('Failed updating 4k_diedai.npk:', e)

    # 2. common.npk (sun & flare transparent in night mode, restored in day/dawn/sunset mode)
    pk_com_path = None if world4k_only else _resolve_target_pack('common.npk')
    if pk_com_path:
        pk_com_bak = pk_com_path + '.orig_day'
        if os.path.isfile(pk_com_path) and not os.path.isfile(pk_com_bak):
            try: shutil.copyfile(pk_com_path, pk_com_bak)
            except Exception: pass

        if os.path.isfile(pk_com_bak):
            try:
                import tools.npk as _npk
                pk_bak = _npk.Pack(pk_com_bak)
                entries = {e.path: e.raw() for e in pk_bak}
                if is_night:
                    pk_base = _npk.Pack(os.path.join(GAME_DIR, 'res', 'common.npk'))
                    sun_hit = pk_base.find('textures/clearsun.dds')
                    flare3_hit = pk_base.find('textures/flare_03.dds')
                    flare1_hit = pk_base.find('textures/flare01.dds')
                    if sun_hit:
                        raw = sun_hit[0].raw()
                        entries['textures/clearsun.dds'] = raw[:128] + b'\x00\x00\x00\x00\xff\xff\xff\xff' * ((len(raw)-128)//8)
                    if flare3_hit:
                        raw = flare3_hit[0].raw()
                        entries['textures/flare_03.dds'] = raw[:128] + b'\x00' * (len(raw)-128)
                    if flare1_hit:
                        raw = flare1_hit[0].raw()
                        entries['textures/flare01.dds'] = raw[:128] + b'\x00' * (len(raw)-128)
                _build_npk(pk_com_path, entries)
            except Exception as e:
                print('Failed updating common.npk:', e)

    # 3. Environment XML files (high.xml, tiaosan.xml, low.xml)
    try:
        if world4k_only:
            raise StopIteration  # day restore removes these instead
        xml_content = _get_env_xml(mode).strip().encode('utf-8')
        xml_targets = [
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'low.xml'),
        ]
        for xp in xml_targets:
            try:
                os.makedirs(os.path.dirname(xp), exist_ok=True)
                with open(xp, 'wb') as f:
                    f.write(xml_content)
            except Exception: pass
    except StopIteration:
        pass
    except Exception as e:
        print('Failed writing env XMLs:', e)

    # 4. world4k.npk (inject environment directly into the pack)
    if world4k_only:
        _w4k_doc = os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k.npk')
        pk_w4k_path = _w4k_doc if os.path.isfile(_w4k_doc) else None
    else:
        pk_w4k_path = _resolve_target_pack(os.path.join('scene', 'world4k.npk'))
    if pk_w4k_path and os.path.isfile(pk_w4k_path):
        try:
            bak_day_p = pk_w4k_path + '.orig_day_xmls'
            import pickle, tools.npk as _npk
            if not os.path.isfile(bak_day_p):
                pk_w4k = _npk.Pack(pk_w4k_path)
                h_hits = pk_w4k.find('world4k_content/env_info/high.xml')
                t_hits = pk_w4k.find('world4k_content/env_info/tiaosan.xml')
                l_hits = pk_w4k.find('world4k_content/env_info/low.xml')
                tl_hits = pk_w4k.find('world4k_content/env_info/tiaosan_low.xml')
                with open(bak_day_p, 'wb') as bf:
                    pickle.dump({
                        'world4k_content/env_info/high.xml': h_hits[0].raw() if h_hits else b'',
                        'world4k_content/env_info/tiaosan.xml': t_hits[0].raw() if t_hits else b'',
                        'world4k_content/env_info/low.xml': l_hits[0].raw() if l_hits else b'',
                        'world4k_content/env_info/tiaosan_low.xml': tl_hits[0].raw() if tl_hits else b'',
                    }, bf)

            def _update_npk_entries(target_npk, entries_dict):
                with open(target_npk, 'r+b') as fh:
                    magic, count, z1, z2, mode_val, idx = HEADER.unpack(fh.read(HEADER.size))
                    if magic != b'NXPK': return
                    fh.seek(idx)
                    raw_index = bytearray(fh.read(count * RECORD.size))
                    names_bytes = fh.read()
                    names = [n.decode('utf-8', 'replace').replace('\\', '/')
                             for n in names_bytes.split(b'\x00') if n]
                    name_to_idx = {name: i for i, name in enumerate(names)}
                    cur_off = idx
                    fh.seek(cur_off)
                    for n, data in entries_dict.items():
                        if n not in name_to_idx: continue
                        ix = name_to_idx[n]
                        fh.write(data)
                        d_len = len(data)
                        crc = zlib.crc32(data) & 0xffffffff
                        rec = RECORD.pack(0, cur_off, d_len, d_len, crc, crc, 0, 0)
                        raw_index[ix * RECORD.size : (ix + 1) * RECORD.size] = rec
                        cur_off += d_len
                    fh.write(raw_index)
                    fh.write(names_bytes)
                    fh.truncate()
                    fh.seek(20)
                    fh.write(struct.pack('<I', cur_off))

            if mode != "day":
                xml_b = _get_env_xml(mode).strip().encode('utf-8')
                _update_npk_entries(pk_w4k_path, {
                    'world4k_content/env_info/high.xml': xml_b,
                    'world4k_content/env_info/tiaosan.xml': xml_b,
                    'world4k_content/env_info/low.xml': xml_b,
                    'world4k_content/env_info/tiaosan_low.xml': xml_b,
                })
                print('world4k.npk updated to %s environment' % mode.upper())
            else:
                day_dict = {}
                if os.path.isfile(bak_day_p):
                    try:
                        with open(bak_day_p, 'rb') as bf: day_dict = pickle.load(bf)
                    except Exception: pass
                if not day_dict:
                    xml_day_b = _DAY_ENV_XML.strip().encode('utf-8')
                    day_dict = {
                        'world4k_content/env_info/high.xml': xml_day_b,
                        'world4k_content/env_info/tiaosan.xml': xml_day_b,
                        'world4k_content/env_info/low.xml': xml_day_b,
                        'world4k_content/env_info/tiaosan_low.xml': xml_day_b,
                    }
                _update_npk_entries(pk_w4k_path, day_dict)
                print('world4k.npk restored to DAY environment')
        except Exception as e:
            print('Failed updating world4k.npk env:', e)



if __name__ == "__main__":
    _mode = sys.argv[4] if len(sys.argv) > 4 else "day"
    _apply_day_night_npk_files(_mode)
    print("weather packs: done (%s)" % _normalize_env_mode(_mode))
