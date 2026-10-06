Below are all plotting/visualization snippets found in the provided Gamma example, summarized individually.

Plot 1: Picks over time by latitude, colored by phase type (P vs S)
- What is plotted
  - X-axis: picks["phase_time"] (timestamp of each pick)
  - Y-axis: picks["latitude"] (station latitude for the pick)
  - Color: picks["phase_type"] mapped via {"P": "red", "S": "blue"}
  - Point size: s=10
  - Legend: created using two empty scatter calls for “P” (red) and “S” (blue)
- How it’s plotted
  - Matplotlib scatter plot, rendered inline in a Jupyter environment
- Inputs and outputs
  - Inputs:
    - DataFrame picks with columns:
      - phase_time (datetime-like)
      - latitude (float)
      - phase_type (string: “P” or “S”)
    - color mapping dict: {"P": "red", "S": "blue"}
  - Outputs:
    - A new matplotlib Figure (plt.figure())
    - A scatter PathCollection of the pick points
    - A legend with two entries (“P”, “S”)
    - Immediate rendering via plt.show()
- Code that produces the figure
  ```python
  # figure the picks (x-axis: time, y-axis: latitude)
  plt.figure()
  color = {"P": "red", "S": "blue"}
  plt.scatter(picks["phase_time"], picks["latitude"], c=picks["phase_type"].apply(lambda x: color[x]), s=10)
  plt.scatter([], [], c="red", label="P")
  plt.scatter([], [], c="blue", label="S")
  plt.legend()
  plt.show()
  ```
- Purpose/interpretation
  - Visual check of the temporal-spatial distribution of picks and the separation of P vs S phases using color.

Plot 2: Associated picks over time by latitude, colored by event index (local run)
- What is plotted
  - X-axis: picks_["phase_time"]
  - Y-axis: picks_["latitude"]
  - Color: picks_["event_index"] mapped to “C{event_index}” for assigned picks; black for unassigned (-1)
  - Point size: s=10
- How it’s plotted
  - Matplotlib scatter plot; created with plt.figure() and plt.scatter()
- Inputs and outputs
  - Inputs:
    - DataFrame picks_ (result from run_gamma) with columns:
      - phase_time (datetime-like)
      - latitude (float)
      - event_index (int; -1 for unassigned)
    - Color mapping function: lambda x: f"C{x}" if x != -1 else "black"
  - Outputs:
    - A new matplotlib Figure
    - A scatter PathCollection of picks colored by event assignment
    - No legend and no explicit plt.show() in the snippet
- Code that produces the figure
  ```python
  plt.figure()
  mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
  plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
  ```
- Purpose/interpretation
  - Visualize which picks are associated with which event after local Gamma association. Unassigned picks are black; each event gets a distinct default matplotlib cycle color (C0, C1, …).

Plot 3: Associated picks over time by latitude, colored by event index (FastAPI run)
- What is plotted
  - X-axis: picks_["phase_time"] (converted back to datetime)
  - Y-axis: picks_["latitude"]
  - Color: picks_["event_index"] mapped to “C{event_index}”; black for unassigned (-1)
  - Point size: s=10
- How it’s plotted
  - Matplotlib scatter plot, same style and mapping as Plot 2
- Inputs and outputs
  - Inputs:
    - DataFrame events = pd.DataFrame(result["events"]) (not plotted here)
    - DataFrame picks_ = pd.DataFrame(result["picks"]) with columns:
      - phase_time (converted to datetime via pd.to_datetime)
      - latitude (float)
      - event_index (int)
    - Color mapping function: lambda x: f"C{x}" if x != -1 else "black"
  - Outputs:
    - A new matplotlib Figure
    - A scatter PathCollection of picks colored by event assignment returned from the API
    - No legend and no explicit plt.show() in the snippet
- Code that produces the figure
  ```python
  # figure the associated events
  events = pd.DataFrame(result["events"])
  picks_ = pd.DataFrame(result["picks"])
  picks_["phase_time"] = pd.to_datetime(picks_["phase_time"])

  plt.figure()
  mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
  plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
  ```
- Purpose/interpretation
  - Validate and visualize the event association produced by the remote FastAPI Gamma run. Colors differentiate events; black indicates unassigned picks.
