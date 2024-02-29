import aiohttp,asyncio,re,time

class Klei:

    token=""
    platform="Steam"

    def set_token(self,token:str):
        """
        设置token
        :param token: token
        """
        self.token=token
    
    def set_platform(self,platform:str):
        """
        设置平台
        :param platform: 平台名称
        """
        self.platform=platform

    async def get_lobby(self):
        """
        获取大厅列表
        :return: 大厅列表
        """
        url="https://lobby-v2-cdn.klei.com/regioncapabilities-v2.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data=await response.json()
                if "LobbyRegions" in data:
                    data=data["LobbyRegions"]
                    temp=[]
                    for item in data:
                        temp.append(item["Region"])
                    return temp
                return []

    async def get_lobby_data(self,lobby:str):
        """
        获取大厅数据
        :param lobby: 大厅名称
        """
        url=f"https://lobby-v2-cdn.klei.com/{lobby}-{self.platform}.json.gz"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data=await response.json()
                if "GET" in data:
                    return data["GET"]
                else:
                    return []

    async def get_row_data(self,lobby:str,row_id:str):
        """
        获取行数据
        :param lobby: 大厅名称
        :param row_id: 行ID
        """
        url=f"https://lobby-v2-{lobby}.klei.com/lobby/read"
        post={
            "__gameId":"DontStarveTogether",
            "__token":self.token,
            "query":{
                "__rowId":row_id,
                "region":lobby
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url,json=post) as response:
                data=await response.json()
                if "GET" in data:
                    return data["GET"]
                else:
                    return []
        
    async def world(self,lobby:str,filter:str=''):
        """
        获取世界列表
        :param lobby: 大厅名称
        :param filter: 名称过滤
        """
        data=await self.get_lobby_data(lobby)
        world_data=[]
        for item in data:
            # 为其添加大厅和平台属性
            item['lobby']=lobby
            item['platform']=self.platform
            # print(f"{item['guid']} -> {item['name']} ({item['connected']}/{item['maxconnections']}) #{lobby}")
            if filter:
                # 判断name是否包含filter
                if filter in item['name']:
                    world_data.append(item)
            else:
                world_data.append(item)
        return world_data

    async def player(self,row_data:dict):
        """
        获取玩家信息
        :param row_data: 行数据
        """
        # 通过正则表达式匹配出“return {“和“}”之间的内容
        pattern=re.compile(r'^return \{(.*?)\}$',re.S)
        result=re.findall(pattern,row_data['players'])
        if not result:
            return []
        # 匹配出“{“和“}”之间的内容
        pattern=re.compile(r'\{(.*?)\}',re.S)
        players=[]
        result=re.findall(pattern,result[0])
        for player in result:
            # 通过正则表达式匹配出name="和"之间的内容以及netid="和"之间的内容
            pattern=re.compile(r'name=\"(.*?)\",.*?netid=\"(.*?)\",.*?prefab=\"(.*?)\"',re.S)
            result=re.findall(pattern,player)
            for name,netid,prefab in result:
                players.append({"name":name,"netid":netid,"prefab":prefab})
        return players

async def main():
    start_time=time.time()
    klei=Klei()
    klei.set_token("这里填写你的token,可以通过申请Klei联机服务器获取")
    lobby=await klei.get_lobby()
    tasks=[]
    # 创建任务
    for item in lobby:
        task=asyncio.create_task(klei.world(item))
        tasks.append(task)
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    # 获取任务结果
    wodrld_data=[]
    for task in tasks:
        wodrld_data+=await task
    print(wodrld_data)
    if not wodrld_data:
        return
    # 取出第一个世界查询具体信息
    row_data=await klei.get_row_data(wodrld_data[0]['lobby'],wodrld_data[0]['__rowId'])
    print(row_data)
    if row_data:
        # 获取玩家信息
        player_data=await klei.player(row_data[0])
        print(player_data)
    print(f"耗时: {time.time()-start_time}s")

asyncio.run(main())