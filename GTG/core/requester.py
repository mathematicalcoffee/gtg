# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Getting Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2009 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

"""
A nice general purpose interface for the datastore and tagstore
"""

import gobject


from GTG.core.tagstore     import Tag
from GTG.tools.logger      import Log

class Requester(gobject.GObject):
    """A view on a GTG datastore.

    L{Requester} is a stateless object that simply provides a nice API for
    user interfaces to use for datastore operations.

    Multiple L{Requester}s can exist on the same datastore, so they should
    never have state of their own.
    """

    __string_signal__ = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str, ))

    __gsignals__ = {'task-added' : __string_signal__, \
              'task-deleted'     : __string_signal__, \
              'task-modified'    : __string_signal__, \
              'task-tagged'      : __string_signal__, \
              'task-untagged'    : __string_signal__, \
              'tag-added'        : __string_signal__, \
              'tag-deleted'      : __string_signal__, \
              'tag-path-deleted' : __string_signal__, \
              'tag-modified'     : __string_signal__}

    def __init__(self, datastore,global_conf):
        """Construct a L{Requester}."""
        gobject.GObject.__init__(self)
        self.ds = datastore
        self.__config = global_conf
        self.__basetree = self.ds.get_tasks_tree()
        
        #TODO build filters here
        self.counter_call = 0
        self.searchActive = False

    ############# Signals #########################
    #Used by the tasks to emit the task added/modified signal
    #Should NOT be used by anyone else
    def _task_loaded(self, tid):
        print "requester send signal : task-added for %s" %tid
        gobject.idle_add(self.emit, "task-added", tid)

        
    ############ Tasks Tree ######################
    # By default, we return the task tree of the main window
    def get_tasks_tree(self,name='active',refresh=True):
        return self.__basetree.get_viewtree(name=name,refresh=refresh)

    def get_main_view(self):
        return self.__basetree.get_main_view()
    
    def get_search_tree(self,name='search',refresh=True):
        """
        return the search tree
        only used by search operations to show a tree without interfering with the main
        """
        return self.__basetree.get_viewtree(name=name,refresh=refresh)
        
    # This is a FilteredTree that you have to handle yourself.
    # You can apply/unapply filters on it as you wish.
#    def get_custom_tasks_tree(self,name=None,refresh=True):
#        return self.__basetree.get_viewtree(name=name,refresh=refresh)
        
    def is_displayed(self,task):
        return self.__basetree.get_viewtree(name='active').is_displayed(task)

    ######### Filters bank #######################
    # List, by name, all available filters
    def list_filters(self):
        return self.__basetree.list_filters()
    
    # Add a filter to the filter bank
    # Return True if the filter was added
    # Return False if the filter_name was already in the bank
    def add_filter(self,filter_name,filter_func):
        return self.__basetree.add_filter(filter_name,filter_func)
        
    # Remove a filter from the bank.
    # Only custom filters that were added here can be removed
    # Return False if the filter was not removed
    def remove_filter(self,filter_name):
        return self.__basetree.remove_filter(filter_name)

    ############## Tasks ##########################
    ###############################################
    def has_task(self, tid):
        """Does the task 'tid' exist?"""
        return self.ds.has_task(tid)

    def get_task(self, tid):
        """Get the task with the given C{tid}.

        If no such task exists, create it and force the tid to be C{tid}.

        @param tid: The task id.
        @return: A task.
        """
        task = self.ds.get_task(tid)
        return task

    def new_task(self, tags=None, newtask=True):
        """Create a new task.

        Note: this modifies the datastore.

        @param pid: The project where the new task will be created.
        @param tags: The tags for the new task. If not provided, then the
            task will have no tags. Tags must be an iterator type containing
            the tags tids
        @param newtask: C{True} if this is creating a new task that never
            existed, C{False} if importing an existing task from a backend.
        @return: A task from the data store
        """
        task = self.ds.new_task()
        if tags:
            for t in tags:
                assert(isinstance(t, Tag) == False)
                task.tag_added(t)
        self._task_loaded(task.get_id())
        return task

    def delete_task(self, tid,recursive=True):
        """Delete the task 'tid' and, by default, delete recursively
        all the childrens.

        Note: this modifies the datastore.

        @param tid: The id of the task to be deleted.
        """
        #send the signal before actually deleting the task !
        Log.debug("deleting task %s" % tid)
        task = self.get_task(tid)
        if task:
            for tag in task.get_tags():
                self.emit('tag-modified', tag.get_name())
        return self.__basetree.del_node(tid,recursive=recursive)
    
    def get_all_titles(self, lowercase=False):
        """
        Gets the titles from all tasks
        
        if lowercase, titles are return in lowercase :)
        """
        titles = []
        nodes = self.get_main_view().get_all_nodes()
        if lowercase:
            for x in nodes:
                titles.append(self.get_main_view().get_node(x).get_title().lower())
        else:
            for x in nodes:
                titles.append(self.get_main_view().get_node(x).get_title())
        return titles
    
    def get_first_task(self, tree='search'):
        """
        returns the first task from a treeview
        
        default is a search view
        """
        nodes = self.get_search_tree(tree,False).get_all_nodes()
        if len(nodes)>0:
            return nodes[0]
        
    ############### Tags ##########################
    ###############################################
    
    def search_is_active(self):
        """
        returns if there is a search active or not
        
        used mainly for stoping certain actions before a search is done
        """
        return self.searchActive
    
    def set_search_status(self, status):
        """
        sets the status of searches
        """
        self.searchActive = status

    def get_tag_tree(self):
        return self.ds.get_tagstore().get_viewtree(name='activetags')
    
    def new_tag(self, tagname):
        """Create a new tag called 'tagname'.

        Note: this modifies the datastore.

        @param tagname: The name of the new tag.
        @return: The newly-created tag.
        """
        return self.ds.new_tag(tagname)
    
    def new_view(self, viewname, params):
        """
        Similar to the above
        Create a new view with the given name.
        Note: this modifies the datastore.
        
        @param viename: The name of the new view.
        @param param:   parameters of the search to save
        @return:        The newly-created view.
        """
        return self.ds.new_view(viewname, params)
    
    def remove_view(self, viewname):
        """
        calls datastore to remove the given view
        """
        self.ds.remove_view(viewname)
    
    def rename_tag(self, oldname, newname):
        self.ds.rename_tag(oldname, newname)

    def get_tag(self, tagname):
        return self.ds.get_tag(tagname)

    def get_notag_tag(self):
        print "no tag not implemented"
        return None
#        return self.ds.get_tagstore().get_notag_tag()

    def get_alltag_tag(self):
        print "all tag not implemented"
        return None
#        return self.ds.get_tagstore().get_alltag_tag()

    def get_used_tags(self):
        """Return tags currently used by a task.

        @return: A list of tag names used by a task.
        """
        l = []
        view = self.ds.get_tagstore().get_viewtree(name='activetags')
        l = view.get_all_nodes()
        l.sort(cmp=lambda x, y: cmp(x.lower(),y.lower()))
        return l
    
    def get_all_tags(self):
        """
        Gets all tags from all tasks
        """
        tags = self.ds.get_tagstore().get_main_view().get_all_nodes()
        return tags
    
    def get_view_names(self):
        """
        returns the names of all views
        """
        return self.ds.get_view_control_names()
    
    def get_view_dic(self):
        """
        returns the dic of all views and params
        """
        return self.ds.get_view_dic()

    ############## Backends #######################
    ###############################################

    def get_all_backends(self, disabled = False):
        return self.ds.get_all_backends(disabled)

    def register_backend(self, dic):
        return self.ds.register_backend(dic)

    def flush_all_tasks(self, backend_id):
        return self.ds.flush_all_tasks(backend_id)

    def get_backend(self, backend_id):
        return self.ds.get_backend(backend_id)

    def set_backend_enabled(self, backend_id, state):
        return self.ds.set_backend_enabled(backend_id, state)

    def remove_backend(self, backend_id):
        return self.ds.remove_backend(backend_id)

    def backend_change_attached_tags(self, backend_id, tags):
        return self.ds.backend_change_attached_tags(backend_id, tags)

    def save_datastore(self):
        return self.ds.save()
        
    ############## Config ############################
    ##################################################
    def get_global_config(self):
        return self.__config
        
    def get_config(self,name):
        return self.__config.get_subconfig(name)
    
    def save_config(self):
        self.__config.save()
