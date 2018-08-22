# -*- coding: utf-8 -*-

from delphin.mrs.util import etree_tostring

def test_etree_tostring():
    import xml.etree.ElementTree as etree
    e = etree.Element('a')
    e.text = 'a'
    assert etree_tostring(e, encoding='unicode') == u'<a>a</a>'
    e.text = u'あ'
    assert etree_tostring(e, encoding='unicode') == u'<a>あ</a>'
    e.text = 'あ'
    assert etree_tostring(e, encoding='unicode') == u'<a>あ</a>'
    b = etree.SubElement(e, 'b')
    b.text = 'あ'
    assert etree_tostring(e, encoding='unicode') == u'<a>あ<b>あ</b></a>'
