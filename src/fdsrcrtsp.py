#! /usr/bin/python

# pyrtsp - RTSP test server hack
# Copyright (C) 2013  Robert Swain <robert.swain@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import gi
gi.require_version('Gst','1.0')
gi.require_version('GstVideo','1.0')
gi.require_version('GstRtspServer','1.0')
from gi.repository import GObject, Gst, GstVideo, GstRtspServer

Gst.init(None)

video_pipeline = Gst.Pipeline.new("video_pipeline")

source = Gst.ElementFactory.make("fdsrc", 'source')
source.set_property('fd', 0)

parsing = Gst.ElementFactory.make("videoparse", "parsing")
parsing.set_property("width",640)
parsing.set_property("height",360)
parsing.set_property("framerate",Gst.Fraction(30,1) )
parsing.set_property("format",16)

vc = Gst.ElementFactory.make("autovideoconvert", "vc")

om = Gst.ElementFactory.make("omxh264enc", "om")
om.set_property("low-latency", True)

payl = Gst.ElementFactory.make("rtph264pay","payl")
payl.set_property("name","pay0")
payl.set_property("pt",96)

for ele in (source, parsing, vc, om, payl):
    video_pipeline.add(ele)
    
source.link(parsing)
parsing.link(vc)
vc.link(om)
om.link(payl)

mainloop = GObject.MainLoop()

server = GstRtspServer.RTSPServer()
server.set_service('5800')

mounts = server.get_mount_points()

#rtsp_media = GstRtspServer.RTSPMedia()
#rtsp_media.take_pipeline(video_pipeline)

factory = GstRtspServer.RTSPMediaFactory()
rtsp_media = factory.do_construct('test')
rtsp_media.take_pipeline(video_pipeline)
#factory.do_media_configure(rtsp_media)

# factory.set_launch('( fdsrc fd=0 ! videoparse width=640 height=360 framerate=30/1 format=16 ! autovideoconvert ! omxh264enc tune=zerolatency ! rtph264pay name=pay0 pt=96 )')

mounts.add_factory("/test", factory)

server.attach(None)

print "stream ready at rtsp://server_address:5800/test"
mainloop.run()
