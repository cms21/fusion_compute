from dotenv import load_dotenv
from utils import get_flows_client
from start_fusion_flow import machine_settings
import os
from dateutil.parser import parse
from matplotlib import pyplot as plt
import numpy as np

load_dotenv(dotenv_path="./fusion.env")
client_id = os.getenv("CLIENT_ID")
flow_id = os.getenv("GLOBUS_FLOW_ID")


fc = get_flows_client(client_id=client_id)
available_machines = machine_settings.keys()
plt.rcParams['xtick.direction'] = plt.rcParams['ytick.direction'] = "in"
color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']


def plot_vs_nparts(run_timings,yvalue_label="flow_run_time",yvalue_norm=None, ylabel="Flow Run Time (s)", ax=None):

    savefig = False
    if not ax:
        fig,ax = plt.subplots()
        plotname = "perf_"+yvalue_label
        if yvalue_norm:
            plotname += "_per_"+yvalue_norm
        plotname += ".pdf"
        savefig = True

    testing_machines = np.unique([run_timings[rt]["machine"] for rt in run_timings])
    
    colors = {}
    xvalues = {}
    yvalues = {}

    c = 0
    for machine in testing_machines:
        colors[machine] = color_cycle[c]
        xvalues[machine] = [run_timings[rt]["nparts"] 
                            for rt in run_timings if run_timings[rt]["machine"] == machine]
        yvalues[machine] = [run_timings[rt][yvalue_label]
                            for rt in run_timings if run_timings[rt]["machine"] == machine]
        if yvalue_norm:
            norms = [run_timings[rt][yvalue_norm] 
                     for rt in run_timings if run_timings[rt]["machine"] == machine]
            yvalues[machine] = [yvalues[machine][i]/norms[i] for i in range(len(norms))]
        c+=1

    for machine in testing_machines:
        ax.loglog(xvalues[machine],yvalues[machine],'s',c=colors[machine],label=machine)

    
    ax.set_xlabel("Particle Count")
    if ylabel:
        ax.set_ylabel(ylabel)
    if savefig:
        ax.legend(loc=0)
        fig.tight_layout()
        fig.savefig(plotname,format="pdf")

def plot_actions_per_nparts(run_timings, actions = ["Make_Inputs", "Transfer_In", "IonOrb", "Postprocessing", "Transfer_Out"]):

    fig = plt.figure()

    axes = {}
    i = 1
    for action in actions:
        axes[action] = fig.add_subplot(3,2,i,title=action)
        axes[action].set_title(action)
        plot_vs_nparts(run_timings,yvalue_label=action, ylabel=None, ax=axes[action])
        i+= 1
    axes["flow"] = fig.add_subplot(3,2,6,title="Flow time")
    plot_vs_nparts(run_timings, ylabel=None, ax=axes["flow"])

    for panel in axes.keys():
        ax = axes[panel]
        ylim = ax.get_ylim()
        ylim = [min(1,min(ylim)),max(ylim)]
        ax.set_ylim(ylim)

    axes["flow"].legend(loc=0)
    fig.tight_layout()
    plt.savefig("perf_actions_per_nparts.pdf",format="pdf")

    return

def plot_actions(run_timings, actions = ["Make_Inputs", "Transfer_In", "IonOrb", "Postprocessing", "Transfer_Out"]):

    fig = plt.figure()

    #fig, ax = plt.subplots()

    #testing_machines = np.unique([run_timings[rt]["machine"] for rt in run_timings])
    testing_machines = ["polaris","perlmutter"]

    colors = {}
    c = 0
    for machine in testing_machines:
        colors[machine] = color_cycle[c]
        ax = fig.add_subplot(2,1,c+1)
        for i,action in enumerate(actions):
            yvalues = [run_timings[rt][action] 
                       for rt in run_timings if run_timings[rt]["machine"] == machine]
            xvalues = [i for n in range(len(yvalues))]
            if i == 0:
                ax.plot(xvalues,yvalues,'s',c=colors[machine],label=machine)
            else:
                ax.plot(xvalues,yvalues,'s',c=colors[machine])
        c+=1
        ax.set_xticks(range(len(actions)))
        ax.set_xticklabels(actions)
        ax.legend(loc=0)
        ax.set_ylabel("Action Time (s)")
    fig.savefig("perf_actions.pdf",format="pdf")
    return

def plot_ionorb_timings(run_timings):

    fig = plt.figure()
    #fig, ax = plt.subplots()

    #testing_machines = np.unique([run_timings[rt]["machine"] for rt in run_timings])
    testing_machines = ["polaris","perlmutter"]
    colors = {}

    c = 0
    
    function_values = [run_timings[rt]["ionorb_function_time"] 
                   for rt in run_timings]
    action_values = [run_timings[rt]["IonOrb"] 
                   for rt in run_timings]
            
    min_val = min(min(function_values),min(action_values))
    max_val = max(max(function_values),max(action_values))



    for machine in testing_machines:
        colors[machine] = color_cycle[c]
        ax = fig.add_subplot(2,1,c+1)
        yvalues = [run_timings[rt]["ionorb_function_time"] 
                   for rt in run_timings if run_timings[rt]["machine"] == machine]
        xvalues = [run_timings[rt]["IonOrb"] 
                   for rt in run_timings if run_timings[rt]["machine"] == machine]
            
        #ax.plot(xvalues,yvalues,'s',c=colors[machine],label=machine)
        ax.hist(yvalues,histtype="step",color=colors[machine],ls='-',label=machine+"-function",range=(min_val,max_val),bins=20)
        ax.hist(xvalues,histtype="step",color=colors[machine],ls='--',label=machine+"-action",range=(min_val,max_val),bins=20)
            
        if c == 0:
            ax.set_title("Ionorb")
        c+=1
        ax.legend(loc=0)
        ax.set_xlabel("Run Time (s)")
        #ax.set_ylabel("Function Time (s)")
        

    fig.savefig("ionorb_timings.pdf",format="pdf")

    return


def parse_flow_action_log(run_id):

    events = {}
    has_next_page = True
    marker = None
    while has_next_page:
        log = fc.get_run_logs(run_id,marker=marker)
        has_next_page = log["has_next_page"]
        if has_next_page:
            marker = log["marker"]
        
        for event in log['entries']:
            code = event["code"]
            time = event["time"]
            if "Flow" in code:
                state_name = code
            else:
                state_name = event["details"]["state_name"]
            if state_name in events.keys():
                events[state_name] = {code:time,**events[state_name]}
            else:
                events[state_name] = {code:time}
      
    return events

def return_flow_times(run_id):

    events = parse_flow_action_log(run_id)
    run_info = fc.get_run(run_id)

    states = events.keys()
    return_times = {}

    return_times["status"] = run_info["status"]

    if run_info["status"] != "SUCCEEDED":
        return return_times

    for state in states:
        state_events = events[state]
        if "ActionStarted" in state_events.keys() and "ActionCompleted" in state_events.keys():
            t = (parse(state_events["ActionCompleted"]) - parse(state_events["ActionStarted"])).total_seconds()
            return_times[state] = t
    
    flow_run_time = (parse(events["FlowSucceeded"]["FlowSucceeded"]) - 
                     parse(events["FlowStarted"]["FlowStarted"])).total_seconds()
    return_times["flow_run_time"] = flow_run_time

    label = run_info["label"]
    return_times["machine"] = label.split("_")[0]

    nparts = run_info["details"]["output"]["input"]["inputs_function_kwargs"]["nparts"]
    return_times["nparts"] = int(nparts)

    ionorb_function_time = run_info["details"]["output"]["IonOrbOutput"]["details"]["result"][0][-1]
    return_times["ionorb_function_time"] = float(ionorb_function_time)

    return return_times

def return_run_list_timings(runs):
    run_timings = {}
    for run_id in runs:
        timings = return_flow_times(run_id)
        if timings["status"] == "SUCCEEDED":
            run_timings[run_id] = timings
    print(run_timings)
    return run_timings

def make_plots(runs, type="all"):

    print("Making Plots")
    run_timings = return_run_list_timings(runs)
    print("Retrieved Run Timings")

    plot_vs_nparts(run_timings)
    plot_vs_nparts(run_timings,yvalue_norm="nparts",ylabel="Flow Run Time per Particle (s)")
    plot_actions_per_nparts(run_timings)

    plot_actions(run_timings)
    plot_ionorb_timings(run_timings)

    return

