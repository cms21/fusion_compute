from dotenv import load_dotenv
from fusion_compute import ENV_PATH
from fusion_compute.utils import get_flows_client
from fusion_compute.machine_settings import machine_settings
import os
import argparse
from dateutil.parser import parse
from matplotlib import pyplot as plt
import numpy as np

load_dotenv(dotenv_path=ENV_PATH)
client_id = os.getenv("CLIENT_ID")
flow_id = os.getenv("GLOBUS_FLOW_ID")


fc = get_flows_client(client_id=client_id)
available_machines = machine_settings().keys()
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
        print(f"Saving {plotname}")
        plt.close(fig)

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
    filename = "perf_actions_per_nparts.pdf"
    fig.savefig(filename,format="pdf")
    print(f"Saving {filename}")
    plt.close(fig)
    return

def plot_actions(run_timings, testing_machines = None, actions = ["Make_Inputs", "Transfer_In", "IonOrb", "Postprocessing", "Transfer_Out"]):

    fig = plt.figure()

    #fig, ax = plt.subplots()

    if testing_machines is None:
        testing_machines = np.unique([run_timings[rt]["machine"] for rt in run_timings])
    
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
    filename = "perf_actions.pdf"
    fig.savefig(filename,format="pdf")
    print(f"Saving {filename}")
    plt.close(fig)
    return

def plot_ionorb_timings(run_timings,testing_machines=None):

    fig = plt.figure()
    #fig, ax = plt.subplots()

    if testing_machines is None:
        testing_machines = np.unique([run_timings[rt]["machine"] for rt in run_timings])
    
    colors = {}

    c = 0
    
    function_values = [run_timings[rt]["ionorb_function_time"] 
                   for rt in run_timings]
    action_values = [run_timings[rt]["IonOrb"] 
                   for rt in run_timings]
            
    min_val = min(min(function_values),min(action_values))
    max_val = max(max(function_values),max(action_values))

    #ratios = [(run_timings[rt]["IonOrb"]-run_timings[rt]["ionorb_function_time"])*100./run_timings[rt]["ionorb_function_time"]
    #                    for rt in run_timings]

    ratios = [run_timings[rt]["IonOrb"]/run_timings[rt]["ionorb_function_time"]
                        for rt in run_timings]
        
    min_rval = min(ratios)
    max_rval = max(ratios)
        

    for machine in testing_machines:
        colors[machine] = color_cycle[c]
        ax_values = fig.add_subplot(2,2,c+c+1)
        print(ax_values)
        function_values = [run_timings[rt]["ionorb_function_time"] 
                            for rt in run_timings if run_timings[rt]["machine"] == machine]
        action_values = [run_timings[rt]["IonOrb"] 
                        for rt in run_timings if run_timings[rt]["machine"] == machine]
        ratios = [run_timings[rt]["IonOrb"]/run_timings[rt]["ionorb_function_time"]
                        for rt in run_timings if run_timings[rt]["machine"] == machine]
        
        
        ax_values.hist(function_values,histtype="step",color=colors[machine],ls='-',label=machine+"-function",range=(min_val,max_val),bins=20)
        ax_values.hist(action_values,histtype="step",color=colors[machine],ls='--',label=machine+"-action",range=(min_val,max_val),bins=20)
        
        ax_ratios = fig.add_subplot(2,2,c+c+2)
        ax_ratios.hist(ratios,histtype="step",color=colors[machine],ls='--',label=machine,bins=20,range=(min_rval,max_rval))
        
        if c == 0:
            ax_values.set_title("Ionorb")
        
        ax_values.legend(loc=0)
        ax_values.set_xlabel("Run Time (s)")
        ax_ratios.set_xlabel("Action/Function Run Time Ratio")
        #ax.set_ylabel("Function Time (s)")
        c+=1

    fig.tight_layout()
    filename = "ionorb_timings.pdf"
    fig.savefig(filename,format="pdf")
    plt.close(fig)
    print(f"Saving {filename}")
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
    return run_timings

def make_plots(runs, type="all", testing_machines=None):

    print("Making Plots")
    run_timings = return_run_list_timings(runs)
    print("Retrieved Run Timings")

    plot_vs_nparts(run_timings)
    plot_vs_nparts(run_timings,yvalue_norm="nparts",ylabel="Flow Run Time per Particle (s)")
    plot_actions_per_nparts(run_timings)

    plot_actions(run_timings,testing_machines=testing_machines)
    plot_ionorb_timings(run_timings,testing_machines=testing_machines)

    return

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--machine', default='polaris', help=f'Target machine for flow', choices=machine_settings().keys())
    parser.add_argument('--test-label', default='796fKLmE', help=f'8 character test label id')
    parser.add_argument('--test-file', default=None, help=f'npy file with test run ids')
    
    return parser.parse_args()


if __name__ == '__main__':

    args = arg_parse()

    test_label = args.test_label
    print(test_label)

    if args.test_file is None:
        run_ids = []
      
        has_next_page = True
        marker = None
        
        while has_next_page:
            runs = fc.list_runs(query_params={"filter_label":args.test_label},marker=marker)
            has_next_page = runs["has_next_page"]
            if has_next_page:
                marker = runs["marker"]
            page_run_ids = [r["run_id"] for r in runs if r["status"] == 'SUCCEEDED']
            for r in runs:
                print(r["label"])
            run_ids += page_run_ids        
            print(f"Found {len(run_ids)} runs in test {test_label}")
    else:
        run_ids = np.load(args.test_file)
        print(f"Found {len(run_ids)} runs in test {test_label}")
        
    make_plots(run_ids,testing_machines=["polaris"])

