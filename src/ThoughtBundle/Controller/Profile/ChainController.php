<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Type\ChainType;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Chain;

/**
 * @Route("/profile")
 */
class ChainController extends Controller
{
    public function navigationAction(Request $request)
    {
        $navigation   = [];
        $navigation[] = [
            'label' => $this->get('translator')->trans('user.chain.list_page.menu_title'),
            'route' => 'sonata_user_chains',
        ];
        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.menu_favorite_chains'),
            'route' => 'sonata_user_favorite_chains',
        ];

        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.public_chains'),
            'route' => 'sonata_user_shared_chains',
        ];
        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.collective_chains'),
            'route' => 'chain_collective',
        ];

        if ($request->get('routeName') == 'chain_page') {
            return $this->render('@Thought/Profile/menu.html.twig', [
                'menu'      => $navigation,
                'routeName' => $request->get('routeName'),
            ]);
        }

        return $this->render(
            '@Thought/Profile/Chains/chainNavigation.html.twig',
            [
                'menu'      => $navigation,
                'routeName' => $request->get('routeName'),
            ]
        );
    }

    public function rightSidebarAction(Request $request, $curTopicId)
    {
        /** @var User $user */
        $user      = $this->getUser();
        $topics    = $user->getTopics();
        $sidebar   = [];
        $sidebar[] = [
            'label' => 'Mes sujets',
            'route' => 'sonata_user_chains',
        ];

        foreach ($topics as $topic) {
            $sidebar[] = [
                'label'      => $topic->getName(),
                'route'      => 'sonata_user_chain_by_topic',
                'parameters' => [
                    'topicId' => $topic->getId(),
                ],
            ];
        }

//        dump($sidebar); die;

        return $this->render('@Thought/Profile/menu.html.twig', [
            'menu'       => $sidebar,
            'routeName'  => $request->get('routeName'),
            'curTopicId' => $curTopicId,
        ]);
    }

    /**
     * @Route("/chains", name="sonata_user_chains")
     * @Route("/student/{user_id}/chains", name="student_chains")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request, User $student = null)
    {
        $user = $this->getUser();
        $em = $this->getDoctrine()->getManager();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
        }

        $chains = $em->getRepository('ThoughtBundle:Chain')->findBy([
            'user' => $user,
        ]);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );

        $renderVariables = [
            'chains' => $pagination,
        ];

        if (!is_null($student)) {
            $renderVariables['student'] = $student;
        }

        return $this->render('ThoughtBundle:Profile/Chains:list.html.twig', $renderVariables);
    }

    /**
     * @Route("/chains/favorite", name="sonata_user_favorite_chains")
     * @Route("/student/{user_id}/chains/favorite", name="student_favorite_chains")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function favoriteAction(Request $request, User $student = null)
    {
        $user = $this->getUser();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
        }

        $em         = $this->getDoctrine()->getManager();
        $chains     = $em->getRepository('ThoughtBundle:Chain')->getAllFavoriteChains($user);
        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );
        return $this->render('ThoughtBundle:Profile/Chains:list.html.twig', [
            'chains' => $pagination,
            'student' => $student
        ]);
    }

    /**
     * @Route("/chains/changefavorite", name="sonata_user_change_favorite")
     * @param Request $request
     * @return RedirectResponse
     */
    public function changeFavoriteAction(Request $request)
    {
        $em    = $this->getDoctrine()->getManager();
        $id    = $request->get('id');
        $chain = $em->getRepository('ThoughtBundle:Chain')->find($id);

        if (!$chain) {
            $this->addFlash('danger', $this->get('translator')->trans('thought.chain.not_exist'));
            return $this->redirect($this->generateUrl('sonata_user_favorite_chains'));
        }

        $favorite = $chain->getFavorite() ? false : true;
        $message  = $favorite ? 'thought.chain.successfully-removed-from-favorites' : 'thought.chain.successfully-added-to-favorites';

        $chain->setFavorite($favorite);

        $em->persist($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans($message));

        return $this->redirect($this->generateUrl('sonata_user_favorite_chains'));
    }

    /**
     * @Route("/chains/{topicId}", name="sonata_user_chain_by_topic", requirements={"chainId"="\d+"})
     *
     * @param int $topicId
     *
     * @return Response
     */
    public function listByTopicAction($topicId, Request $request)
    {
        $chains = $this->getDoctrine()->getRepository(Chain::class)->findBy([
            'topic' => $topicId,
        ]);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );

        $routeName = $request->get('_route');

        return $this->render('ThoughtBundle:Profile/Chains:list.html.twig', [
            'chains'    => $pagination,
            'routeName' => $routeName,
        ]);
    }

    /**
     * @Route("/chain/create", name="sonata_user_chain_create")
     *
     * @param Request $request
     *
     * @return Response
     */
    public function createAction(Request $request)
    {
        $chain = new Chain();
        $em    = $this->getDoctrine()->getManager();

        $role = User::ROLE_USER;

        if ($this->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        $form = $this->createForm(new ChainType(), $chain, [
            'role' => $role,
        ]);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $chain->setUser($this->getUser());
                $em->persist($chain);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ThoughtBundle:Profile/Chains:create.html.twig', [
            'form' => $form->createView(),
        ]);
    }

    /**
     * @Route("/chain/{chainId}/edit", name="sonata_user_chain_edit", requirements={"chainId"="\d+"})
     * @ParamConverter("chain", options={"mapping"={"chainId"="id"}})
     * @param Request $request
     * @param int     $chainId
     *
     * @return RedirectResponse|Response
     */
    public function editAction(Request $request, $chainId, Chain $chain)
    {
        $this->denyAccessUnlessGranted('edit', $chain);
        $em = $this->getDoctrine()->getManager();
        $chainOwner = $chain->getUser();
        $student = null;
        $role = User::ROLE_USER;

        if ($this->isGranted('ROLE_TEACHER') and ($this->getUser() !== $chainOwner)) {
            $student = $chainOwner;
            $role = User::ROLE_STUDENT;
        }

        $role = User::ROLE_USER;
        if ($this->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        $form = $this->createForm(new ChainType(), $chain, [
            'role' => $role,
        ]);

        $form->handleRequest($request);

        if ($request->getMethod() == 'POST' && $form->isValid()) {
            $chain->setUser($chainOwner);
            if ($chain->getIsPrivate()) {
                $chain->setTopic(null);
            }
            $em->persist($chain);
            $em->flush();

            if (!is_null($student)) {
                return $this->redirect($this->generateUrl('student_chains', ['user_id' => $student->getId()]));
            } else {
                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ThoughtBundle:Profile/Chains:edit.html.twig', [
            'form' => $form->createView(),
            'student' => $student,
        ]);
    }

    /**
     * @Route("/chain/{chainId}/remove", name="sonata_user_chain_remove", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     *
     * @return RedirectResponse
     */
    public function removeAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $em->remove($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.successfully-remove'));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/{chainId}/share", name="sonata_user_chain_share", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     *
     * @return RedirectResponse
     */
    public function shareAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));
            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));
            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $private = $chain->getIsPrivate();

        if ($private == true) {
            $chain->setIsPrivate(false);
        } else {
            $chain->setIsPrivate(true);
            $chain->setIsCollective(false);
        }

        $shareMessage = $private ? 'successfully-shared' : 'successfully-private';

        $em->persist($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.' . $shareMessage));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/{chainId}/collective", name="sonata_user_chain_collective", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     *
     * @return RedirectResponse
     */
    public function collectiveAction($chainId)
    {
        $em    = $this->getDoctrine()->getManager();
        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);
        if ($chain->getIsPrivate() == false) {
            if (!$this->checkOwner($chain)) {
                $this->addFlash('danger', $this->get('translator')->trans('thought.chain.access_denied'));
                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }

            $collective        = $chain->getisCollective();
            $collective        = $collective ? false : true;
            $collectiveMessage = $collective ? 'successfully-collectiveded' : 'successfully-personalised';

            $chain->setIsCollective($collective);

            $em->persist($chain);
            $em->flush();
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.' . $collectiveMessage));
        }
        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/collective", name="chain_collective")
     */
    public function listCollectiveAction(Request $request)
    {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $em = $this->getDoctrine()->getManager();

        $role = $this->getUser()->getRole();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllCollectiveChains($role);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('@Thought/Profile/Chains/collectiveList.html.twig', [
            'chains' => $pagination,

        ]);
    }

    /**
     * @Route("/shared-chains", name="sonata_user_shared_chains")
     * @param Request $request
     * @return Response
     */
    public function listSharedAction(Request $request)
    {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $em = $this->getDoctrine()->getManager();

        $role = $this->getUser()->getRole();
        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllSharedChains($role);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('@Thought/Profile/Chains/sharedList.html.twig', [
            'chains' => $pagination,

        ]);
    }

    /**
     * @param Request $request
     *
     * @return Response
     */
    public function publicListSharedAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllSharedChains();

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('@Thought/Profile/Chains/publicSharedList.html.twig', [
            'chains' => $pagination,
        ]);
    }

    /**
     * Check owner chain
     *
     * @param Chain $chain
     *
     * @return bool
     */
    private function checkOwner(Chain $chain)
    {
        return $chain->getUser()->getId() == $this->getUser()->getId() ? true : false;
    }
}
