/**
 *  This class contains backbone wrappers for basic ui elements such as Images, Labels, Buttons, Input fields etc.
 */
define(['utils/utils',
    ],
    function( Utils ) {


    /** Renders an input element used e.g. in the tool form */
    var WebComponent = Backbone.View.extend({
        initialize: function( options ) {
            this.model = options && options.model || new Backbone.Model({
                template       : null,
                type            : 'text',
                placeholder     : '',
                disabled        : false,
                visible         : true,
                cls             : '',
                area            : false,
                color           : null,
                style           : null,
                template_loaded : false
            }).set( options );
            this.webcomponent = '<script src="/plugins/visualization/polymer/bower_components/webcomponentsjs/webcomponents-lite.js"></script><link rel="import" href="/plugins/visualization/polymer/test-app/'+this.model.get('template')+'.html"><'+this.model.get('template')+'></'+this.model.get('template')+'>';
            this.tagName = this.model.get( 'template' );
            this.setElement( $( '<' + this.tagName + '/>' ) );
            this.listenTo( this.model, 'change', this.render, this );
            this.render();
        },
        events: {
            'input': '_onchange'
        },
        value: function( new_val ) {
            new_val !== undefined && this.model.set( 'value', typeof new_val === 'string' ? new_val : '' );
            return this.model.get( 'value' );
        },
        render: function() {
            if(! this.model.template_loaded) {
                this.$el.prepend('<script src="/static/polymer/bower_components/webcomponentsjs/webcomponents-lite.js"></script><link rel="import" href="/static/polymer/test-app/'+this.model.get('template')+'.html">');
                this.model.template_loaded = true;
            }
            this.$el.removeClass()
                    .addClass( this.model.get( 'cls' ) )
                    .addClass( this.model.get( 'style' ) )
                    .attr( 'galaxyid', this.model.id )
                    .attr( 'galaxyplaceholder', this.model.get( 'placeholder' ) )
                    .css( 'color', this.model.get( 'color' ) || '' )
                    .css( 'border-color', this.model.get( 'color' ) || '' );
            if ( this.model.get( 'value' ) !== this.$el.attr('galaxyvalue') ) {
                this.$el.attr( 'galaxyvalue', this.model.get( 'value' ) );
            }
            this.model.get( 'disabled' ) ? this.$el.attr( 'disabled', true ) : this.$el.removeAttr( 'disabled' );
            this.$el[ this.model.get( 'visible' ) ? 'show' : 'hide' ]();
            return this;
        },
        _onchange: function() {
            this.value( this.$("#"+this.model.id).val() );
            this.model.get( 'onchange' ) && this.model.get( 'onchange' )( this.model.get( 'value' ) );
        }
    });

    return {
        WebComponent       : WebComponent
    }
});
