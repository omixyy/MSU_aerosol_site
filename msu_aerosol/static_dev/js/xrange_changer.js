function updateGraph() {
    var startDate = document.getElementById('datetime_picker_start').value;
    var endDate = document.getElementById('datetime_picker_end').value;
    var update = {
      'xaxis.range': [startDate, endDate]
    }
    Plotly.relayout(document.getElementsByClassName("plotly-graph-div")[0].id, update);
  }
