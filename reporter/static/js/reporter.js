
/* Update stats */
L.Control.UpdateStats = L.Control.extend({

    onAdd: function (map) {
        var className = 'leaflet-control-stats',
            container = L.DomUtil.create('div', className),
            option,
            choice;

        L.DomEvent.disableClickPropagation(container);
        var div = L.DomUtil.create('div', "", container);
        var select = L.DomUtil.create('select', "", div);
        for (var i = 0, l = this.options.choices.length; i<l; i++) {
            option = L.DomUtil.create('option', "", select);
            choice = this.options.choices[i];
            option.value = option.innerHTML = choice;
            if (choice == this.options.selected) {
                option.selected = "selected";
            }
        }

        var link = L.DomUtil.create('a', "", container);
        link.href = '#';
        link.innerHTML = "&nbsp;";
        link.title = "Get stats for this view";
        var fn = function (e) {
            var bounds = map.getBounds(),
                bbox = bounds.toBBoxString();
            window.location = "?bbox=" + bbox + "&obj=" + select.value;
        };

        L.DomEvent
            .on(link, 'click', L.DomEvent.stopPropagation)
            .on(link, 'click', L.DomEvent.preventDefault)
            .on(link, 'click', fn, map)
            .on(link, 'dblclick', L.DomEvent.stopPropagation);

        return container;
    }
});

L.Map.addInitHook(function () {
    if (this.options.updateStatsControl) {
        var options = this.options.statsControlOptions ? this.options.statsControlOptions : {};
        this.updateStatsControl = new L.Control.UpdateStats(options);
        this.addControl(this.updateStatsControl);
    }
});

$(function(){
  $('.view-hm').click(function(e){
    var username = $(this).attr("data-user");
    $.ajax("/user", {
      data: {username: username,
             bbox: window.bbox},
      success: function(data){
        if (window.hmlayer) {
          window.map.removeLayer(window.hmlayer);
        }
        var heatmap = new L.TileLayer.HeatCanvas({},{'step':0.07, 'degree':HeatCanvas.LINEAR, 'opacity':0.7});
        $.each(data.d, function(i,e){
          heatmap.pushData(e[0], e[1], 1);
        })
        window.map.addLayer(heatmap);
        window.hmlayer = heatmap;
      }
    });
  });

  $('.clear-hm').click(function(e){
    if (window.hmlayer) {
      window.map.removeLayer(window.hmlayer);
      delete window.hmlayer;
    }
  });

  // Set up detail row hiding etc.

  $('.details-toggle').click(function(e){
        var rowId = $(this).attr("value");
        $("#"+rowId).toggle();
  });
  $('#all-details').click(function(e){
        var status = $(this).attr("checked");
        if (status)
        {
            $(".details-row").show();
        }
        else
        {
            $(".details-row").hide();
        }
        $('.details-toggle').attr("checked", status);
  });
});

