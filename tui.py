def home_screen(versions: dict, platform: str):
  logo = f"""
              ████               | 
              ████               | █▀█ █▄█ █▀█ ▄▀█ █▀▄▀█ █ █▀▄
            ██░░████             | █▀▀  █  █▀▄ █▀█ █ ▀ █ █ █▄▀
            ██░░████             | Minecraft launcher
          ██░░██    ██           | 
          ██░░██    ██           | by Romyx
        ██░░░░██      ██         | 
        ██░░░░██      ██         | Platform: {platform}
      ██░░░░░░██        ██       | MC versions found: {len(versions)}
      ██░░░░██          ██       | Latest version of MC: {list(versions)[0].split("-", 1)[1]}
    ██░░░░░░██            ██     |
    ██░░░░░░██            ██     |
  ██░░░░░░░░██              ██   |
  ██░░░░░░██                ██   |
██░░░░░░░░██                  ██ |
████████████████████████████████ |\n"""
  print(logo)

