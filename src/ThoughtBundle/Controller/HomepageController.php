<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Class HomepageController
 * @package ThoughtBundle\Controller
 */
class HomepageController extends Controller
{
    /**
     * @Route("/", methods={"GET"})
     *
     * @param Request $request
     * @return Response
     */
    public function indexAction(Request $request)
    {
        $start = microtime(true);

        $page = $request->query->getInt('page', 1);

        $countItem = 10;

        $modelThought = $this->container->get('thought.model.thought_model');

        $finder = $this->container->get('fos_elastica.finder.app.thought');

        $thoughts = $modelThought->getThoughtsFromElastic($request->get('search'), $finder, $page, $countItem);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $thoughts,
            $page,
            $countItem
        );

        $timeExecute = microtime(true) - $start;

        return $this->render('ThoughtBundle::homepage.html.twig', array(
            'thoughts'    => $pagination,
            'timeExecute' => $timeExecute,
        ));
    }

    /**
     * @Route("/parse")
     *
     * @return Response
     */
    public function parseAction()
    {
        $parseService = $this->container->get('thought.parser.service')->testParse();

        return new Response('');
    }

    /**
     * @Route("/instruction", name="instruction")
     * @return Response
     */
    public function instructionAction()
    {
        return $this->render('@Thought/instruction.html.twig');
    }
}
