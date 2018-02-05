import Deferred from "utils/deferred";
import Modal from "mvc/ui/ui-modal";
import Chart from "mvc/visualization/chart/components/model";
import Editor from "mvc/visualization/chart/views/editor";
import Viewer from "mvc/visualization/chart/views/viewer";

export default Backbone.View.extend({
    initialize: function(options) {
        this.options = options;
        this.modal = (window.parent.Galaxy && window.parent.Galaxy.modal) || new Modal.View();
        this.setElement("<div/>");
        $.ajax({
            url: `${Galaxy.root}api/datasets/${options.dataset_id}`
        })
            .done(dataset => {
                this.dataset = dataset;
                this.chart = new Chart({}, options);
                this.chart.plugin = options.visualization_plugin;
                this.chart.plugin.specs = this.chart.plugin.specs || {};
                this.chart_load = options.chart_load;
                this.deferred = new Deferred();
                this.viewer = new Viewer(this);
                this.editor = new Editor(this);
                this.$el.append(this.viewer.$el);
                this.$el.append(this.editor.$el);
                this.go("viewer");
                this.chart.load();
                this.chart.trigger("redraw");
            })
            .fail(response => {
                let message = response.responseJSON && response.responseJSON.err_msg;
                this.errormessage = message || "Import failed for unkown reason.";
            });
    },

    /** Loads a view and makes sure that all others are hidden */
    go: function(view_id) {
        $(".tooltip").hide();
        this.viewer.hide();
        this.editor.hide();
        this[view_id].show();
    }
});
