from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.playlist import M3UPlaylist

m3u_plus_attributes = {
    "x-tvg-url": "http://myown.link:80/luke/220311/22311"
}
m3u_plus_channel_0 = IPTVChannel(
    url="http://myown.link:80/luke/210274/78482",
    name="Rai 1",
    duration="-1",
    attributes={
        IPTVAttr.TVG_ID.value: "Rai 1",
        IPTVAttr.TVG_NAME.value: "Rai 1",
        IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
        IPTVAttr.GROUP_TITLE.value: "RAI"
    }
)
m3u_plus_channel_1 = IPTVChannel(
    url="http://myown.link:80/luke/210274/89844",
    name="Cielo",
    duration="-1",
    attributes={
        IPTVAttr.TVG_ID.value: "",
        IPTVAttr.TVG_NAME.value: "Cielo",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Italia"
    },
    extras=[
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
    ]
)
m3u_plus_channel_2 = IPTVChannel(
    url="http://myown.link:80/luke/109163/89800",
    name="TEMATICO MASSIMO TROISI",
    duration="-1",
    attributes={
        IPTVAttr.TVG_ID.value: "",
        IPTVAttr.TVG_NAME.value: "TEMATICO MASSIMO TROISI",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Italia",
        IPTVAttr.TVG_SHIFT.value: "-0.5"
    }
)
m3u_plus_channel_3 = IPTVChannel(
    url="http://myown.link:80/luke/109163/78282",
    name="----I N T R A T T E N I M E N T O----",
    duration="-1",
    attributes={
        IPTVAttr.TVG_ID.value: "-10.5",
        IPTVAttr.TVG_NAME.value: "----I N T R A T T E N I M E N T O----",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Intrattenimento"
    }
)
expected_m3u_plus = M3UPlaylist()
expected_m3u_plus._attributes = m3u_plus_attributes
expected_m3u_plus._channels = [
    m3u_plus_channel_0,
    m3u_plus_channel_1,
    m3u_plus_channel_2,
    m3u_plus_channel_3
]

expected_m3u_plus_group_by_group_title = {
    "RAI": [0],
    "Italia": [1, 2],
    "Intrattenimento": [3]
}
expected_m3u_plus_group_by_url = {
    "http://myown.link:80/luke/210274/78482": [0],
    "http://myown.link:80/luke/210274/89844": [1],
    "http://myown.link:80/luke/109163/89800": [2],
    "http://myown.link:80/luke/109163/78282": [3]
}

expected_m3u8_list = [
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/564",
        name="CA: HBO",
        duration="-1",
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/559",
        name="CA: NBC HD",
        duration="-1",
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/560",
        name="CA: PBS KIDS HD",
        duration="-1",
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/601",
        name="SANTUÁRIO DE FÁTIMA",
        duration="-1",
    )
]
expected_m3u8 = M3UPlaylist()
expected_m3u8._channels = expected_m3u8_list

split_quoted_string = """#EXTM3U x-tvg-url="http://myown.link:80/luke/220311/22311"
#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1
" tvg-logo="https://static.epg.best/it/RaiUno.it.png" group-title="RAI",Rai 1
http://myown.link:80/luke/210274/78482
#EXTINF:-1 tvg-id="" tvg-name="Cielo" tvg-logo="" group-title="Italia",Cielo
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0
http://myown.link:80/luke/210274/89844
#EXTINF:-1 tvg-id="" tvg-name="TEMATICO MASSIMO TROISI" tvg-logo="" group-title="Italia
" tvg-shift="-0.5",TEMATICO MASSIMO TROISI
http://myown.link:80/luke/109163/89800
#EXTINF:-1 tvg-id="-10.5
" tvg-name="----I N T R A T T E N I M E N T O----" tvg-logo="" group-title="Intrattenimento",----I N T R A T T E N I M E N T O----
http://myown.link:80/luke/109163/78282"""

unquoted_attributes = """#EXTM3U x-tvg-url="http://myown.link:80/luke/220311/22311"
#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" tvg-logo="https://static.epg.best/it/RaiUno.it.png" group-title="RAI",Rai 1
http://myown.link:80/luke/210274/78482
#EXTINF:-1 tvg-id="" tvg-name="Cielo" tvg-logo="" group-title="Italia",Cielo
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0
http://myown.link:80/luke/210274/89844
#EXTINF:-1 tvg-id="" tvg-name="TEMATICO MASSIMO TROISI" tvg-logo="" group-title="Italia" tvg-shift=-0.5,TEMATICO MASSIMO TROISI
http://myown.link:80/luke/109163/89800
#EXTINF:-1 tvg-id=-10.5 tvg-name="----I N T R A T T E N I M E N T O----" tvg-logo="" group-title="Intrattenimento",----I N T R A T T E N I M E N T O----
http://myown.link:80/luke/109163/78282"""

expected_urlencoded_list = [
    IPTVChannel(
        url="http://myown.link:80/luke/109163/78281",
        name="Vacanze 83",
        duration="-1",
        attributes={"tvg-logo": "https://some.image.service.com/images/V1_UY268_CR4%2C0%2C182%2C268_AL_.jpg"}
    ),
    IPTVChannel(
        url="http://myown.link:80/luke/109163/78282",
        name="Vacanze 90",
        duration="-1",
        attributes={"tvg-logo": "https://some.image.service.com/images/%2C%2C%2C%2C%2C.png"}
    ),
    IPTVChannel(
        url="http://myown.link:80/luke/109163/78283",
        name="Vacanze 91",
        duration="-1",
        attributes={"tvg-logo": "https://some.image.service.com/images/vacanze.jpg"}
    ),
    IPTVChannel(
        url="http://myown.link:80/luke/109163/78284",
        name="Vacanze 95",
        duration="-1",
        attributes={"tvg-logo": "https://some.image.service.com/images/M/MV5BOTVkOWExNmYtZDdjMy00ODlhLTlhMTYtMjRmYzRhMmMwZWRlXkEyXkFqcGdeQXVyMzU0NzkwMDg%40._V1_UY268_CR2%2C0%2C182%2C268_AL_.jpg"}
    )
]
expected_urlencoded = M3UPlaylist()
expected_urlencoded._channels = expected_urlencoded_list

broken_extinf_row = """#EXTINF:-1 tvg-id="" tvg-name=""AR || Wonderful! || "RR" tvg-logo="https://img.mysite.net/5425.jpg" group-title="free, stream","AR || Wonderful! || "RR"""
expected_attributes_broken_extinf_row = {
    'tvg-id': '',
    'tvg-name': '_AR || Wonderful! || _RR',
    'tvg-logo': 'https://img.mysite.net/5425.jpg',
    'group-title': 'free, stream'
}

space_before_comma = """#EXTM3U url-tvg="http://epg.51zmt.top:8000/e.xml" catchup="append" catchup-source="?playseek=${(b)yyyyMMddHHmmss}-${(e)yyyyMMddHHmmss}"

#EXTINF:10 ,channel name 0
http://myown.link:80/luke/109163/78280
#EXTINF:-11  ,channel name 1
http://myown.link:80/luke/109163/78281
#EXTINF:12 ,channel name 2
http://myown.link:80/luke/109163/78282
#EXTINF:13.0   ,channel name 3
http://myown.link:80/luke/109163/78283
"""
