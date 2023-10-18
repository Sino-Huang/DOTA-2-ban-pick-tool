import requests

def main():
    heroes = []

    with open('hero_wide_icons/names.txt', 'r') as f:
        for line in f:
            hero = line.strip().split(', ')
            heroes.append(hero)

    arr = [{
        'name': hero[0],
        'alt_name': hero[1],
        'filename': hero[1] + '.png',
    } for hero in heroes]

    for hero in arr:
        filename = hero['filename']
        url = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/%s'%filename
        response = requests.get(url)
        if response.status_code == 200:
            with open('hero_wide_icons/%s'%filename, 'wb') as f:
                print('Downloaded: %s'%(filename))
                f.write(response.content)
        else:
            print('Failed to download: %s'%(filename))

if __name__ == '__main__':
    main()