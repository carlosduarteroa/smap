import pygtk
pygtk.require('2.0')
import gtk
import gobject
import requests
import json
gtk.gdk.threads_init()

def getlatestvalue(path):
    try:
        resp = requests.get(path)
        if not resp.ok:
            return "Error: " + resp.reason
        data = json.loads(resp.content)
        return str(data['Readings'][-1][-1])
    except:
        return "Error"
    
    

class Device:
    def callback(self, widget, data=None):
        """
        Naive callback that just prints the input args
        """
        print "input: {0}".format(data)

    def delete_event(self, widget, event, data=None):
        """
        Callback that starts the teardown of GTK
        """
        gtk.main_quit()
        return False
    
    def __init__(self, title, imagepath, source_uri, readrate):
        """
        Lays the groundwork for creating a GUI for this sMAP driver.
        Creates window with a [title] and connects the delete_event callback.
        This will not render the window until we call self.finish()

        [source_uri] is something like "localhost:8080/data"; and is the root
        URI of where the sMAP source is running. All paths specified later are
        relative to this
        """
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(title)
        self.window.connect("delete_event",self.delete_event)
        self.window.set_border_width(20)

        self.imagepath = imagepath
        self.readrate = int(readrate * 1000)
        self.uri = source_uri

        self.timeseries = {}

    def add_timeseries(self, path, label, with_actuator=False):
        """
        Adds a row to the GUI that corresponds to the latest value
        of the sMAP path [path]. The value will be labeled with [label].

        If [with_actuator] is True, then it will also attempt to visit
        {path}_act and render a column for an actuator for that timeseries.
        It will use the actuator metadata to render an appropriate interface
        """
        #TODO: use the actuators
        self.timeseries[path] = label

    def adjust_image(self, path, fxn):
        def _get_val_for_img(path):
            latest = getlatestvalue(self.uri+path)
            self.image.clear()
            self.image.set_from_file(fxn(latest))
            self.image.show()
            return True
        gobject.timeout_add(self.readrate, lambda : _get_val_for_img(path))

    def add_table(self):
        """
        After you have finished adding timeseries, calling add_table
        will render those timeseries on the GUI
        """
        #TODO: discover how many columns
        self.cols = 2
        self.rows = len(self.timeseries) + 2 # add 2 for the image and the quit button
        self.table = gtk.Table(self.cols, self.rows, False)
        self.window.add(self.table)

        # add the quit button to the bottom
        button = gtk.Button("Quit")
        button.connect("clicked", lambda w: gtk.main_quit())
        self.table.attach(button, 0, self.cols, self.rows-1, self.rows, yoptions=gtk.SHRINK)
        button.show()

        # add the image to the top
        self.image = gtk.Image()
        self.image.set_from_file(self.imagepath)
        self.table.attach(self.image, 0, self.cols, 0, 1)
        self.image.show()

        for idx, path in enumerate(self.timeseries):
            # add label to first column
            self.add_label(path, 0, 1, idx+1, idx+2)


    def _update(self, labelobj, label, path):
        """
        Loopable callback that fetches the latest value from sMAP and puts it in a label
        3 args:
        [labelobj]: the actual GTK lable object we're changing
        [label]: the name we prepend to the value
        [path]: the URI path relative to self.uri where we decode the sMAP JSON reading
        """
        latest = getlatestvalue(self.uri+path)
        labelobj.set_text(label+': '+latest)
        return True

    def add_label(self, path, xstart, xend, ystart, yend):
        """
        Add a self-updating label for [path] at the specified position
        """
        label = gtk.Label(self.timeseries[path])
        self.table.attach(label, xstart, xend, ystart, yend, yoptions=gtk.SHRINK)
        gobject.timeout_add(self.readrate, lambda : self._update(label, self.timeseries[path], path))
        label.show()

    def add_button(self, name, xstart, xend, ystart, yend, callback, args):
        button = gtk.Button(name)
        button.connect("clicked", callback, *args)
        self.table.attach(button, xstart, xend, ystart, yend, yoptions=gtk.SHRINK)
        button.show()


    def finish(self):
        self.table.show()
        self.window.show()

def main():
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()

if __name__ == '__main__':
    hello = Device()
    main()
