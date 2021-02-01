from app.model.channel import IPTVChannel, IPTVAttr
from app.model.playlist import M3UPlaylist

m3u_plus_channel_0 = IPTVChannel(
    url="http://myown.link:80/luke/210274/78482",
    name="Rai 1",
    duration=-1,
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
    duration=-1,
    attributes={
        IPTVAttr.TVG_ID.value: "",
        IPTVAttr.TVG_NAME.value: "Cielo",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Italia"
    }
)
m3u_plus_channel_2 = IPTVChannel(
    url="http://myown.link:80/luke/109163/89800",
    name="TEMATICO MASSIMO TROISI",
    duration=-1,
    attributes={
        IPTVAttr.TVG_ID.value: "",
        IPTVAttr.TVG_NAME.value: "TEMATICO MASSIMO TROISI",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Italia"
    }
)
m3u_plus_channel_3 = IPTVChannel(
    url="http://myown.link:80/luke/109163/78282",
    name="----I N T R A T T E N I M E N T O----",
    duration=-1,
    attributes={
        IPTVAttr.TVG_ID.value: "",
        IPTVAttr.TVG_NAME.value: "----I N T R A T T E N I M E N T O----",
        IPTVAttr.TVG_LOGO.value: "",
        IPTVAttr.GROUP_TITLE.value: "Intrattenimento"
    }
)
expected_m3u_plus = M3UPlaylist()
expected_m3u_plus.list = [
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

expected_m3u8 = M3UPlaylist()
expected_m3u8.list = [
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/564",
        name="CA: HBO",
        duration=-1,
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/559",
        name="CA: NBC HD",
        duration=-1,
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/560",
        name="CA: PBS KIDS HD",
        duration=-1,
    ),
    IPTVChannel(
        url="http://myown.link.com:8000/localchannels/jack53ls83j/601",
        name="SANTUÁRIO DE FÁTIMA",
        duration=-1,
    )
]
